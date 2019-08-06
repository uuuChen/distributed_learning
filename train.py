
# System Imports
from __future__ import print_function
import argparse
import torch.optim as optim
from model.AlexNet import *
from torch.autograd import Variable

from dataSet.MNIST_dataSet import *
from dataSet.DRD_dataSet import *
from data.data_args import *

# training settings
parser = argparse.ArgumentParser()

parser.add_argument('--data-name', type=str, default='DRD', metavar='D',
                    help='name of thed data used for training (default: DRD)')

parser.add_argument('--batch-size', type=int, default=5, metavar='N',
                    help='input batch size for training (default: 5)')

parser.add_argument('--epochs', type=int, default=10, metavar='N',
                    help='number of epochs to train (default: 10)')

parser.add_argument('--lr', type=float, default=0.1, metavar='LR',
                    help='learning rate (default: 0.1)')

parser.add_argument('--image-size', type=int, default=(100, 100), metavar='N',
                    help='image size (width, height) for training and testing (default: (100, 100))', nargs='+')

parser.add_argument('--momentum', type=float, default=0.5, metavar='M',
                    help='SGD momentum (default: 0.5)')

parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')

parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')

parser.add_argument('--log-interval', type=int, default=1, metavar='N',
                    help='how many batches to wait before logging training status')

train_args = parser.parse_args(args=[])


def train_epoch(model, dataSet, epoch):

    model.train()

    data_nums = dataSet.get_data_nums_from_database()

    batches = (data_nums - 1) // train_args.batch_size + 1

    for batch_idx in range(1, batches + 1):

        data, target = dataSet.get_data_and_labels(batch_size=train_args.batch_size,
                                                   image_size=tuple(train_args.image_size),
                                                   one_hot=False)

        if train_args.cuda:
            data, target = data.cuda(), target.cuda()

        data, target = Variable(data).float(), Variable(target).long()

        optimizer.zero_grad()

        output = model(data)

        loss = F.nll_loss(output, target)

        loss.backward()

        optimizer.step()

        if batch_idx % train_args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * train_args.batch_size, data_nums,
                       100. * batch_idx / batches, loss.item()))


def test_epoch(model, dataSet):

    model.eval()

    test_loss = 0

    correct = 0

    data_nums = dataSet.get_data_nums_from_database()

    batches = (data_nums - 1) // train_args.batch_size + 1

    for batch_idx in range(1, batches + 1):

        data, target = dataSet.get_data_and_labels(batch_size=train_args.batch_size,
                                                   image_size=tuple(train_args.image_size),
                                                   one_hot=False)

        if train_args.cuda:
            data, target = data.cuda(), target.cuda()

        data, target = Variable(data).float(), Variable(target).long()

        output = model(data)

        test_loss += F.nll_loss(output, target).item()

        pred = output.data.max(1)[1]

        correct += pred.eq(target.data).cpu().sum()

    test_loss /= batches

    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, data_nums,
        100. * correct / data_nums))


if __name__ == '__main__':

    if train_args.data_name == 'MNIST':
        train_dataSet = MNIST_DataSet(data_args=MNIST_TRAIN_ARGS)
        test_dataSet = MNIST_DataSet(data_args=MNIST_TEST_ARGS)
        model = None

    elif train_args.data_name == 'DRD':
        train_dataSet = DRD_DataSet(data_args=DRD_TRAIN_ARGS)
        test_dataSet = DRD_DataSet(data_args=DRD_TEST_ARGS)
        model = AlexNet()

    else:
        raise Exception("data_name ( %s ) not exist !" % train_args.data_name)

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

        train_epoch(model=model,
                    dataSet=train_dataSet,
                    epoch=epoch)

        test_epoch(model=model,
                   dataSet=test_dataSet)




