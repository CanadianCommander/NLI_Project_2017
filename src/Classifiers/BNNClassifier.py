from .ClassifierBase import ClassifierBase, LanguageGroup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC
from sklearn.feature_selection import SelectKBest, SelectFromModel
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import StratifiedKFold
from src.util.Misc import max_index, select_feature
from keras.models import model_from_json
from sklearn.pipeline import Pipeline
import numpy as np
import tensorflow as tf
import os

FEATURE_COUNT = 100000
FEATURE = "original"
N_CLASSES = 11
LOAD_MODEL = False


class BNN:
    def __init__(self, pout=False):
        super(BNN,self).__init__()
        one = _BNN("one")
        one.add_pipe(Pipeline([('cv', CountVectorizer(ngram_range=(2, 2), binary=True)),
                               ('kb', SelectKBest(k=FEATURE_COUNT))]))
        one.add_pipe(Pipeline([('cv', CountVectorizer(ngram_range=(1, 3), binary=True)),
                               ('kb', SelectKBest(k=50000))]))

        two = _BNN("two")
        two.add_pipe(Pipeline([('cv', CountVectorizer(ngram_range=(2, 2), binary=True)),
                               ('kb', SelectKBest(k=FEATURE_COUNT))]))

        three = _BNN("three")
        three.add_pipe(Pipeline([('cv', CountVectorizer(ngram_range=(5, 5), binary=True, analyzer="char")),
                                 ('kb', SelectKBest(k=FEATURE_COUNT))]))

        four = _BNN("four")
        four.add_pipe(Pipeline([('cv', CountVectorizer(ngram_range=(5, 5), binary=True, analyzer="char_wb")),
                                ('kb', SelectKBest(k=FEATURE_COUNT))]))

        self.network_list = [one,two,three,four]
        self.prob_output = pout

    def preprocess(self,data):
        return data


    def train(self,training_data):
        if len(training_data) == 1:
            feature_data = []
            feature_data.append(select_feature(training_data[0][1], training_data[0][0], "original"))
            feature_data.append(select_feature(training_data[0][1], training_data[0][0], "lemmas"))

            i = 0
            #networks = []
            for network in self.network_list:
                print("Training Network: ", i + 1, " of: ", len(self.network_list))
                network.load_from_disk(os.path.join(os.path.dirname(__file__),"BNN1/"))
                network.train(None, feature_data)
                i += 1

            #final = np.ndarray(shape=(networks[0].shape[0],4),dtype=object)
            #for j in range(0,len(networks)):
            #    for i in range(0,len(networks[j])):
            #        final[:,j][i] = list(networks[j][i])

            #np.save("foobar", final)


        else:
            i = 0
            for network in self.network_list:
                print("Training Network: ", i+1, " of: ", len(self.network_list))
                network.train(training_data)
                i += 1

        # save models to disk
        #for network in self.network_list:
        #    network.save_to_disk("/tmp/models/")

    def classify(self,testing_data):
        network_results = []
        label_list = []

        if len(testing_data) == 1:

            feature_data = []
            feature_data.append(select_feature(testing_data[0][1], testing_data[0][0], "original"))
            feature_data.append(select_feature(testing_data[0][1], testing_data[0][0], "lemmas"))

            for data in feature_data[0]:
                label_list.append(data[0])

            i = 0
            for network in self.network_list:
                network_results.append(network.classify(None, feature_data))
                i += 1
        else :
            label_list = []
            for test in testing_data:
                label_list.append(test[0])

            network_results = []
            for network in self.network_list:
                network_results.append(network.classify(testing_data))

        if self.prob_output:
            return network_results
        else:
            output = []
            for i in range(0, len(network_results[0])):
                output_merge = network_results[0][i]
                for z in range(1, len(network_results)):
                    for k in range(0, N_CLASSES):
                        output_merge[k] *= network_results[z][i][k]
                output.append((label_list[i], LanguageGroup.LABEL_MAP_STR[max_index(output_merge)+1]))

            return output



class _BNN (ClassifierBase):
    def __init__(self,name, ngram_range=(1,4),binary=True,analyzer='word',lower=True,feature_count=FEATURE_COUNT):
        super(_BNN, self).__init__()
        self.estimator = None
        self.kbest = SelectKBest(k=feature_count)
        self.cv = CountVectorizer(ngram_range=ngram_range,binary=binary,lowercase=lower,analyzer=analyzer)
        self.sel = SelectFromModel(LinearSVC(C=0.47))
        self.tfid = TfidfTransformer()
        self.pipe_list = []
        self.name = name

    def preprocess(self, data):
        return data

    def add_pipe(self, pipe):
        self.pipe_list.append(pipe)

    def save_to_disk(self,path):
        model_json = self.estimator.to_json()
        with open(os.path.join(path, self.name + ".json"), "w") as jfile:
            jfile.write(model_json)
        self.estimator.save_weights(os.path.join(path, self.name+".h5"))
        print("Model ", self.name, "saved to disk @ ", path)

    def load_from_disk(self, path):
        with open(os.path.join(path, self.name + ".json"), "r") as jfile:
            self.estimator = model_from_json(jfile.read())

        self.estimator.load_weights(os.path.join(path, self.name+".h5"))
        print("Model ", self.name, " loaded from disk")

    def train(self, training_data, feature_list=None):
        from keras.models import Sequential
        from keras.layers import Dense, Activation, Dropout
        from keras.utils import to_categorical
        from keras.callbacks import EarlyStopping

        feature_counts = []
        label_list = []
        if feature_list is not None:
            # format data for DNN
            for data in feature_list[0]:
                label_list.append(LanguageGroup.LABEL_MAP[data[0][2]] - 1)

            feature_mtx = []
            i = 0
            for feature in feature_list:
                data_list = []
                for data in feature:
                    data_list.append(data[1])

                if i < len(self.pipe_list) and self.pipe_list[i] is not None:
                    feature_mtx.append(self.pipe_list[i].fit_transform(data_list, label_list).toarray())
                i += 1

            if self.estimator is None:
                feature_counts = feature_mtx[0]
                for i in range(1,len(feature_mtx)):
                    feature_counts = np.concatenate([feature_counts,feature_mtx[i]],axis=1)

        else:
            # format data for DNN
            data_list = []
            for data in training_data:
                label_list.append(LanguageGroup.LABEL_MAP[data[0][2]]- 1)
                data_list.append(data[1])

            # extract features
            feature_counts = self.tfid.fit_transform(self.kbest.fit_transform(self.cv.fit_transform(data_list), label_list),label_list).toarray()

        if self.estimator is None:
            print("feature count: ", feature_counts.shape[1])
            self.estimator = Sequential()
            self.estimator.add(Dense(128,activation='tanh',input_shape=(feature_counts.shape[1],)))
            self.estimator.add(Dropout(0.2))
            self.estimator.add(Dense(N_CLASSES,activation="softmax"))
            self.estimator.compile(loss="categorical_crossentropy",optimizer="Adam", metrics=['accuracy'])
            self.estimator.fit(feature_counts, to_categorical(label_list, num_classes=11),
                               batch_size=64, epochs=2, callbacks=[EarlyStopping(monitor="loss", min_delta=0.1)])

            #out_mtx_lst = np.ndarray(shape=(feature_counts.shape[0],11))
            #skf = StratifiedKFold(n_splits=10)
            #label_list = np.array(label_list)
            #for train_index, test_index in skf.split(feature_counts,label_list):
            #    estimator = Sequential()
            #    estimator.add(Dense(128, activation='tanh', input_shape=(feature_counts.shape[1],)))
            #    estimator.add(Dropout(0.2))
            #    estimator.add(Dense(N_CLASSES, activation="softmax"))
            #    estimator.compile(loss="categorical_crossentropy", optimizer="Adam", metrics=['accuracy'])
            #    estimator.fit(feature_counts[train_index], to_categorical(label_list[train_index], num_classes=11),
            #                       batch_size=64, epochs=2, callbacks=[EarlyStopping(monitor="loss", min_delta=0.1)])
            #    network_results = estimator.predict(feature_counts[test_index])
            #    out_mtx_lst[test_index] = network_results
            #    output = []
            #    labels = label_list[test_index]
            #    i = 0
            #    for row in network_results:
            #        output.append((labels[i], max_index(row)))
            #        i += 1

            #    correct = 0
            #    total = 0
            #    for o in output:
            #        if o[0] == o[1]:
            #            correct += 1
            #        total += 1

            #    print("Accuracy is: ", (float(correct)/float(total)))
            #return out_mtx_lst
        else:
            self.estimator.compile(loss="categorical_crossentropy", optimizer="Adam", metrics=['accuracy'])

    def classify(self, testing_data, feature_list=None):
        output = []
        feature_counts = None
        if feature_list is not None:
            if feature_list is not None:

                feature_mtx = []
                i = 0
                for feature in feature_list:
                    data_list = []
                    for data in feature:
                        data_list.append(data[1])

                    if i < len(self.pipe_list) and self.pipe_list[i] is not None:
                        feature_mtx.append(self.pipe_list[i].transform(data_list).toarray())
                    i += 1

                feature_counts = feature_mtx[0]
                for i in range(1, len(feature_mtx)):
                    feature_counts = np.concatenate([feature_counts, feature_mtx[i]], axis=1)
        else:
            data_list = []
            label_list = []
            for test in testing_data:
                label_list.append(test[0])
                data_list.append(test[1])

            feature_counts = self.tfid.transform(self.kbest.transform(self.cv.transform(data_list))).toarray()

        results = self.estimator.predict(feature_counts)
        return results
