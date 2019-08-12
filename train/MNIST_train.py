
# System Imports
from __future__ import print_function
from torch.autograd import Variable
import argparse
import torchvision
import matplotlib.pyplot as plt

# Model Imports
from model.LeNet import *

# DataSet Imports
from dataSet.MNIST_dataSet import *
from data.data_args import *  # import data arguments

os.chdir('../')

# training settings
parser = argparse.ArgumentParser()

parser.add_argument('--batch-size', type=int, default=128, metavar='N',
                    help='input batch size for training (default: 512)')

parser.add_argument('--epochs', type=int, default=10, metavar='N',
                    help='number of epochs to train (default: 30)')

parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                    help='learning rate (default: 0.01)')

parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                    help='SGD momentum (default: 0.5)')

parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')

parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')

parser.add_argument('--log-interval', type=int, default=1, metavar='N',
                    help='how many batches to wait before logging training status')

train_args = parser.parse_args(args=[])

train_dataSet = MNIST_DataSet(data_args=MNIST_TRAIN_ARGS,
                              shuffle=True)

test_dataSet = MNIST_DataSet(data_args=MNIST_TEST_ARGS,
                             shuffle=True)

model = LeNet()

def train_epoch(epoch):

    model.train()

    data_nums = train_dataSet.get_data_nums_from_database()

    batches = (data_nums - 1) // train_args.batch_size + 1

    datas, targets = train_dataSet.get_data_and_labels(batch_size=train_args.batch_size,
                                                   one_hot=False)
    datas_tratned_num = 0
    for batch_idx in range(1, batches + 1):
        if batch_idx * train_args.batch_size < len(datas):
            data = datas[(batch_idx-1) * train_args.batch_size:batch_idx * train_args.batch_size]
            target = targets[(batch_idx-1) * train_args.batch_size:batch_idx * train_args.batch_size]
        else:
            data = datas[(batch_idx-1) * train_args.batch_size:len(datas)]
            target = targets[(batch_idx-1) * train_args.batch_size:len(datas)]

        if train_args.cuda:
            data, target = data.cuda(), target.cuda()

        data, target = Variable(data).float(), Variable(target).long()

        optimizer.zero_grad()

        output = model(data)

        # #show img
        # print(target)
        # img = torchvision.utils.make_grid(data.cpu())
        # img = img.numpy().transpose(1, 2, 0)
        #
        # std = [0.5, 0.5, 0.5]
        # mean = [0.5, 0.5, 0.5]
        # img = img * std + mean
        # plt.imshow(img)
        # plt.show()

        loss = F.cross_entropy(output, target)

        loss.backward()

        optimizer.step()

        datas_tratned_num += len(data)
        if batch_idx % train_args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, datas_tratned_num, data_nums,
                       100. * batch_idx / batches, loss.item()))


def test_epoch():

    model.eval()

    test_loss = 0

    correct = 0

    data_nums = test_dataSet.get_data_nums_from_database()

    batches = (data_nums - 1) // train_args.batch_size + 1

    datas, targets = test_dataSet.get_data_and_labels(batch_size=train_args.batch_size,
                                                       one_hot=False)

    for batch_idx in range(1, batches + 1):

        data = datas[(batch_idx-1) * train_args.batch_size:batch_idx * train_args.batch_size]
        target = targets[(batch_idx-1) * train_args.batch_size:batch_idx * train_args.batch_size]

        if train_args.cuda:
            data, target = data.cuda(), target.cuda()

        data, target = Variable(data).float(), Variable(target).long()

        output = model(data)

        test_loss += F.cross_entropy(output, target).item()

        pred = output.data.max(1)[1]

        correct += pred.eq(target.data).cpu().sum()

    test_loss /= batches

    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, data_nums,
        100. * correct / data_nums))

if __name__ == '__main__':

    train_args.cuda = not train_args.no_cuda and torch.cuda.is_available()

    torch.manual_seed(train_args.seed)  # seeding the CPU for generating random numbers so that the results are
                                        # deterministic

    if train_args.cuda:
        torch.cuda.manual_seed(train_args.seed)  # set a random seed for the current GPU
        model.cuda()  # move all model parameters to the GPU

    optimizer = optim.SGD(model.parameters(),
                          lr=train_args.lr,
                          momentum=train_args.momentum)

    for epoch in range(1, train_args.epochs + 1):

        train_epoch(epoch=epoch)


        test_epoch()




