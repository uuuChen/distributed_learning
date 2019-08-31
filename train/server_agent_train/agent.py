
import torch
from torch.autograd import Variable

from socket_.socket_ import *
from logger import *

# DataSet Imports
from dataSet.MNIST_dataSet import *
from dataSet.DRD_dataSet import *
from dataSet.Xray_dataSet import *
from dataSet.ECG_dataSet import *
from data.data_args import *  # import data arguments

class Agent(Logger):

    def __init__(self, model, server_host_port, cur_name):
        Logger.__init__(self)
        self.model = model
        self.server_host_port = server_host_port
        self.cur_name = cur_name


    def get_dataSet(self, shuffle):

        data_name = self.train_args.dataSet

        if data_name == 'MNIST':
            dataSet = MNIST_DataSet
            train_data_args = MNIST_TRAIN_ARGS
            test_data_args = MNIST_TEST_ARGS

        elif data_name == 'DRD':
            dataSet = DRD_DataSet
            train_data_args = DRD_TRAIN_ARGS
            test_data_args = DRD_TEST_ARGS

        elif data_name == 'ECG':
            dataSet = ECG_DataSet
            train_data_args = ECG_TRAIN_ARGS
            test_data_args = ECG_TEST_ARGS

        elif data_name == 'Xray':
            dataSet = Xray_DataSet
            train_data_args = Xray_TRAIN_ARGS
            test_data_args = Xray_TEST_ARGS

        else:
            raise Exception('DataSet ( %s ) Not Exist !' % data_name)

        training_args = {}
        training_args['shuffle'] = shuffle
        training_args['is_simulate'] = self.is_simulate

        train_data_args.update(training_args)
        test_data_args.update(training_args)

        self.train_dataSet = dataSet(train_data_args)
        self.test_dataSet = dataSet(test_data_args)

    def _conn_to_server(self):
        # connect to server, agent and server socket setting
        self.agent_server_sock = Socket(self.server_host_port, False)
        self.agent_server_sock.connect()

    def _recv_train_args_from_server(self):
        self.train_args = self.agent_server_sock.recv('train_args')
        self.train_args.cuda = not self.train_args.no_cuda and torch.cuda.is_available()
        self.is_simulate = self.train_args.is_simulate
        if self.is_simulate:
            self.get_dataSet(shuffle=False)  # shuffle or not won't influence the results
        else:
            self.get_dataSet(shuffle=True)  # must shuffle

    def _recv_agents_attrs_from_server(self):
        # receive own IP and distributed port
        self.cur_host_port = self.agent_server_sock.recv('cur_host_port')
        self.to_agent_sock = Socket(self.cur_host_port, True)

        # receive previous, next agents from server
        self.prev_agent_attrs, self.next_agent_attrs = self.agent_server_sock.recv('prev_next_agent_attrs')

    def _send_total_data_nums_to_server(self):
        if self.agent_server_sock.recv('is_first_agent'):
            self._send_data_nums_to_server()

    def _recv_id_list_from_server(self):
        self.train_id_list, self.test_id_list = self.agent_server_sock.recv('train_test_id_list')

    def _training_setting(self):

        if self.is_simulate:
            # set dataSet's "db_id_list" and store train and test data numbers
            self.train_dataSet.set_db_id_list(self.train_id_list)
            self.test_dataSet.set_db_id_list(self.test_id_list)
            train_data_nums = len(self.train_id_list)
            test_data_nums = len(self.test_id_list)
        else:
            train_data_nums = self.train_dataSet.get_data_nums_from_database()
            test_data_nums = self.test_dataSet.get_data_nums_from_database()

        self.train_data_nums = train_data_nums
        self.test_data_nums = test_data_nums

        # seeding the CPU for generating random numbers so that the
        torch.manual_seed(self.train_args.seed)

        # results are deterministic
        if self.train_args.cuda:
            torch.cuda.manual_seed(self.train_args.seed)  # set a random seed for the current GPU
            self.model.cuda()  # move all model parameters to the GPU
        self.optim = torch.optim.SGD(self.model.parameters(),
                                     lr=self.train_args.lr,
                                     momentum=self.train_args.momentum)

    def _send_data_nums_to_server(self):
        train_data_nums = self.train_dataSet.get_data_nums_from_database()
        test_data_nums = self.test_dataSet.get_data_nums_from_database()
        self.agent_server_sock.send(train_data_nums, 'train_data_nums')
        self.agent_server_sock.send(test_data_nums, 'test_data_nums')

    def _send_model_to_next_agent(self):
        # send model to next agent
        self.to_agent_sock.accept()
        self.to_agent_sock.send(self.model, 'agent_model')
        self.to_agent_sock.close()

    def _iter_through_db_once(self, is_training):

        train_str = 'Training' if is_training else 'Testing'

        print('{} starts {}....'.format(self.cur_name, train_str))

        if is_training:
            self.model.train()
            data_nums = self.train_data_nums
            dataSet = self.train_dataSet
            batch_size = self.train_args.train_batch_size
        else:
            self.model.eval()
            data_nums = self.test_data_nums
            dataSet = self.test_dataSet
            batch_size = self.train_args.test_batch_size

        trained_data_num = 0
        batches = (data_nums - 1) // batch_size + 1
        for batch_idx in range(1, batches + 1):

            data, target = dataSet.get_data_and_labels(batch_size=batch_size)

            if self.train_args.cuda:
                data = data.cuda()

            data, target = Variable(data).float(), Variable(target).long()

            # agent forward
            if is_training:
                self.optim.zero_grad()
            agent_output = self.model(data)

            # send agent_output and target to server
            self.agent_server_sock.send(agent_output, 'agent_output')  # send agent_output
            self.agent_server_sock.send(target, 'target')  # send target

            # receive gradient from server if training
            if is_training:
                # get agent_output_clone
                agent_output_grad = self.agent_server_sock.recv('agent_output_clone_grad')

                # agent backward
                agent_output.backward(gradient=agent_output_grad)
                self.optim.step()

            trained_data_num += data.shape[0]
            server_host_port = self.agent_server_sock.getpeername()
            print('{} at {}: [{}/{} ({:.0f}%)]'.format(train_str, server_host_port, trained_data_num, data_nums,
                                                       100.0 * batch_idx / batches))

    def _get_model_from_prev_agent(self):
        print('\nwait for previous agent {} model snapshot...'.format(self.prev_agent_attrs['host_port']))
        if not self.agent_server_sock.recv('is_first_training'):
            from_agent_sock = Socket(self.prev_agent_attrs['host_port'], False)
            from_agent_sock.connect()
            self.model = from_agent_sock.recv('agent_model')
            from_agent_sock.close()

            # VERY IMPORTANT !!! awake server after current agent receiving model snapshot from previous agent
            self.agent_server_sock.awake()
        print('done !\n')

    def _iter(self, is_training):

        self._get_model_from_prev_agent()

        self._iter_through_db_once(is_training=is_training)

        train_str = 'training' if is_training else 'testing'
        print('{} done {} \n'.format(self.cur_name, train_str))

        if is_training:
            self._send_model_to_next_agent()

        else:
            if self.agent_server_sock.recv('is_training_done'):
                # if it is the last agent to test
                if int(self.cur_name.split("_")[1]) is self.train_args.agent_nums:  # no need to send model
                    pass
                else:  # need to send model
                    self._send_model_to_next_agent()
                self.agent_server_sock.close()
                return True
            else:
                self._send_model_to_next_agent()
                return False

    def start_training(self):

        self._conn_to_server()

        self._recv_train_args_from_server()

        self._recv_agents_attrs_from_server()

        if self.is_simulate:
            self._send_total_data_nums_to_server()
            self._recv_id_list_from_server()

        else:
            self._send_data_nums_to_server()

        self._training_setting()

        while True:
            self._iter(is_training=True)
            done = self._iter(is_training=False)
            if done:
                break

           



