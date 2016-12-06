import numpy
import scipy.special


class NeuralNet(object):

    def __init__(self, n_input, n_hidden, n_output, learning_rate):

        self.n_input = n_input
        self.n_hidden = n_hidden
        self.n_output = n_output

        self.learning_rate = learning_rate

        self.wih = numpy.random.normal(0.0, pow(self.n_hidden, -0.5), (self.n_hidden, self.n_input))
        self.who = numpy.random.normal(0.0, pow(self.n_output, -0.5), (self.n_output, self.n_hidden))

    def train(self, inputs_list, targets_list):
        inputs = numpy.array(inputs_list, ndmin=2).T
        targets = numpy.array(targets_list, ndmin=2).T

        hidden_inputs = numpy.dot(self.wih, inputs)
        hidden_outputs = self.activation_function(hidden_inputs)
        final_inputs = numpy.dot(self.who, hidden_outputs)
        final_outputs = self.activation_function(final_inputs)

        output_errors = targets - final_outputs
        hidden_errors = numpy.dot(self.who.T, output_errors)

        self.who += self.learning_rate * numpy.dot(output_errors * final_outputs * (1.0 - final_outputs), numpy.transpose(hidden_outputs))
        self.wih += self.learning_rate * numpy.dot(hidden_errors * hidden_outputs * (1.0 - hidden_outputs), numpy.transpose(inputs))

    def query(self, inputs_list):
        inputs = numpy.array(inputs_list, ndmin=2).T

        hidden_inputs = numpy.dot(self.wih, inputs)
        hidden_outputs = self.activation_function(hidden_inputs)

        final_inputs = numpy.dot(self.who, hidden_outputs)
        final_outputs = self.activation_function(final_inputs)

        return final_outputs

    def activation_function(self, x):
        return scipy.special.expit(x)


if __name__ == '__main__':
    input_nodes = 784
    hidden_nodes = 200
    output_nodes = 10

    learning_rate = 0.1

    nn = NeuralNet(input_nodes, hidden_nodes, output_nodes, learning_rate)

    training_data_file = open('mnist_train.csv', 'r')
    training_data_list = training_data_file.readlines()
    training_data_file.close()

    epochs = 1

    for i in range(epochs):

        for record in training_data_list:
            all_values = record.split(',')
            inputs = (numpy.asfarray(all_values[1:]) / 255.0 * 0.99) + 0.01
            targets = numpy.zeros(output_nodes) + 0.01
            targets[int(all_values[0])] = 0.99
            import ipdb; ipdb.set_trace()
            nn.train(inputs, targets)

    test_data_file = open('mnist_test.csv', 'r')
    test_data_list = test_data_file.readlines()
    test_data_file.close()

    scorecard = []
    for i, record in enumerate(test_data_list):
        all_values = record.split(',')

        correct_label = int(all_values[0])
        inputs = (numpy.asfarray(all_values[1:]) / 255.0 * 0.99) + 0.01
        outputs = nn.query(inputs)

        label = numpy.argmax(outputs)
        if label == correct_label:
            scorecard.append(1)
        else:
            scorecard.append(0)

    scorecard_array = numpy.asarray(scorecard)
    print('performance = ', scorecard_array.sum() / float(scorecard_array.size))
