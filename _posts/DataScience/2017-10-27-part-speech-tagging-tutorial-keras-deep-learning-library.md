---
layout: post
title:  "Part-of-Speech tagging tutorial with the Keras Deep Learning library"
author: axel.bellec
categories: [ en, data science ]
image: "assets/images/DataScience/pos_tagging_neural_nets_keras/blog.jpg"
---
> In this tutorial, you will see how you can use a simple Keras model to train and evaluate an artificial neural network for multi-class classification problems. 

Part-of-Speech tagging is a well-known task in [Natural Language Processing](https://en.wikipedia.org/wiki/Natural_language_processing). It refers to the process of classifying words into their parts of speech (also known as words classes or lexical categories). This is a supervised learning approach.

<div align="center">
  <img src="https://media.giphy.com/media/l2JdWtSlp3Z68ubSM/giphy.gif" alt="giphy_homer"/>
</div>

[Artificial neural networks](https://en.wikipedia.org/wiki/Artificial_neural_network) have been applied successfully to compute POS tagging with great performance. We will focus on the Multilayer Perceptron Network, which is a very popular network architecture, considered as the state of the art on Part-of-Speech tagging problems. 

__Let's put it into practice__ 

In this post you will get a quick tutorial on how to implement a simple Multilayer Perceptron in Keras and train it on an annotated corpus.

### Ensuring reproducibility

In order to be sure that our experiences can be achieved again we need to fix the random seed for reproducibility:  

```python
import numpy as np

CUSTOM_SEED = 42
np.random.seed(CUSTOM_SEED)
```

### Getting an annotated corpus

The [Penn Treebank](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.9.8216&rep=rep1&type=pdf) is an annotated corpus of POS tags. A sample is available in the [`NLTK`](https://github.com/nltk/nltk) python library which contains a lot of corpora that can be used to train and test some NLP models.

First of all, we download the annotated corpus:
```python
import nltk
nltk.download('treebank')
```

Then we load the tagged sentences...
```python
from nltk.corpus import treebank
sentences = treebank.tagged_sents(tagset='universal')
```

... and visualize one:
```python
import random
print(random.choice(sentences))
```
This yields a list of tuples `(term, tag)`.
```
[('Mr.', 'NOUN'), ('Otero', 'NOUN'), (',', '.'), ('who', 'PRON'), ('apparently', 'ADV'), 
('has', 'VERB'), ('an', 'DET'), ('unpublished', 'ADJ'), ('number', 'NOUN'), (',', '.'), 
('also', 'ADV'), ('could', 'VERB'), ("n't", 'ADV'), ('be', 'VERB'), ('reached', 'VERB'), 
('.', '.')]
```

This is a multi-class classification problem with more than forty different classes.
POS tagging on Treebank corpus is a well-known problem and we can expect to achieve a model accuracy larger than 95%.

```python
tags = set([tag for sentence in treebank.tagged_sents() for _, tag in sentence])
print('nb_tags: %s\ntags: %s' % (len(tags), tags))
```

```
46
{'IN', 'VBZ', '.', 'RP', 'DT', 'VB', 'RBR', 'CC', '#', ',', 'VBP', 'WP$', 'PRP', 'JJ', 
'RBS', 'LS', 'PRP$', 'WRB', 'JJS', '``', 'EX', 'POS', 'WP', 'VBN', '-LRB-', '-RRB-', 
'FW', 'MD', 'VBG', 'TO', '$', 'NNS', 'NNPS', "''", 'VBD', 'JJR', ':', 'PDT', 'SYM', 
'NNP', 'CD', 'RB', 'WDT', 'UH', 'NN', '-NONE-'}
```

### Datasets preprocessing for supervised learning


We split our tagged sentences into 3 datasets :  
- a __training dataset__ which corresponds to the sample data used to fit the model,
- a __validation dataset__ used to tune the parameters of the classifier, for example to choose the number of units in the neural network,
- a __test dataset__ used *only* to assess the performance of the classifier.

<div align="center">
  <img src="{{ site.baseurl }}/assets/images/DataScience/pos_tagging_neural_nets_keras/train_test_val.png" alt="train_test_val_split"/>
</div>

We use approximately 60% of the tagged sentences for training, 20% as the validation set and 20% to evaluate our model.

```python
train_test_cutoff = int(.80 * len(sentences)) 
training_sentences = sentences[:train_test_cutoff]
testing_sentences = sentences[train_test_cutoff:]

train_val_cutoff = int(.25 * len(training_sentences))
validation_sentences = training_sentences[:train_val_cutoff]
training_sentences = training_sentences[train_val_cutoff:]
```

### Feature engineering

Our set of features is very simple. 
For each term we create a dictionnary of features depending on the sentence where the term has been extracted from.  
These properties could include informations about previous and next words as well as prefixes and suffixes.  

```python
def add_basic_features(sentence_terms, index):
    """ Compute some very basic word features.

        :param sentence_terms: [w1, w2, ...] 
        :type sentence_terms: list
        :param index: the index of the word 
        :type index: int
        :return: dict containing features
        :rtype: dict
    """
    term = sentence_terms[index]
    return {
        'nb_terms': len(sentence_terms),
        'term': term,
        'is_first': index == 0,
        'is_last': index == len(sentence_terms) - 1,
        'is_capitalized': term[0].upper() == term[0],
        'is_all_caps': term.upper() == term,
        'is_all_lower': term.lower() == term,
        'prefix-1': term[0],
        'prefix-2': term[:2],
        'prefix-3': term[:3],
        'suffix-1': term[-1],
        'suffix-2': term[-2:],
        'suffix-3': term[-3:],
        'prev_word': '' if index == 0 else sentence_terms[index - 1],
        'next_word': '' if index == len(sentence_terms) - 1 else sentence_terms[index + 1]
    }
```

We map our list of sentences to a list of dict features.

```python
def untag(tagged_sentence):
    """ 
    Remove the tag for each tagged term. 
    
    :param tagged_sentence: a POS tagged sentence
    :type tagged_sentence: list
    :return: a list of tags
    :rtype: list of strings
    """
    return [w for w, _ in tagged_sentence]
    

def transform_to_dataset(tagged_sentences):
    """
    Split tagged sentences to X and y datasets and append some basic features.

    :param tagged_sentences: a list of POS tagged sentences
    :param tagged_sentences: list of list of tuples (term_i, tag_i)
    :return: 
    """
    X, y = [], []
    
    for pos_tags in tagged_sentences:
        for index, (term, class_) in enumerate(pos_tags):
            # Add basic NLP features for each sentence term
            X.append(add_basic_features(untag(pos_tags), index))
            y.append(class_)
    return X, y
```

For training, validation and testing sentences, we split the attributes into `X` (input variables) and `y` (output variables).

```python
X_train, y_train = transform_to_dataset(training_sentences)
X_test, y_test = transform_to_dataset(testing_sentences)
X_val, y_val = transform_to_dataset(validation_sentences)
```

### Features encoding

Our neural network takes vectors as inputs, so we need to convert our dict features to vectors. 
`sklearn` builtin function [`DictVectorizer`](http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.DictVectorizer.html) provides a straightforward way to do that.

```python
from sklearn.feature_extraction import DictVectorizer

# Fit our DictVectorizer with our set of features
dict_vectorizer = DictVectorizer(sparse=False)
dict_vectorizer.fit(X_train + X_test + X_val)
```

```python
# Convert dict features to vectors
X_train = dict_vectorizer.transform(X_train)
X_test = dict_vectorizer.transform(X_test)
X_val = dict_vectorizer.transform(X_val)
```

Our `y` vectors must be encoded. The output variable contains 49 different string values that are encoded as integers.

```python
# Fit LabelEncoder with our list of classes
from sklearn.preprocessing import LabelEncoder
label_encoder = LabelEncoder()
label_encoder.fit(y_train + y_test + y_val)
```

```python
# Encode class values as integers
y_train = label_encoder.transform(y_train)
y_test = label_encoder.transform(y_test)
y_val = label_encoder.transform(y_val)
```
And then we need to convert those encoded values to dummy variables (one-hot encoding). 
```python
# Convert integers to dummy variables (one hot encoded)
from keras.utils import np_utils

y_train = np_utils.to_categorical(y_train)
y_test = np_utils.to_categorical(y_test)
y_val = np_utils.to_categorical(y_val)
``` 

### Building a Keras model 

[`Keras`](https://github.com/fchollet/keras/) is a high-level framework for designing and running neural networks on multiple backends like [`TensorFlow`](https://github.com/tensorflow/tensorflow/), [`Theano`](https://github.com/Theano/Theano) or [`CNTK`](https://github.com/Microsoft/CNTK).

<div align="center">
  <img src="{{ site.baseurl }}/assets/images/DataScience/pos_tagging_neural_nets_keras/keras.png" alt="keras_logo"/>
</div>

We want to create one of the most basic neural networks: the Multilayer Perceptron. This kind of linear stack of layers can easily be made with the `Sequential` model. This model will contain an input layer, an hidden layer, and an output layer.   
To overcome overfitting, we use dropout regularization. We set the dropout rate to 20%, meaning that 20% of the randomly selected neurons are ignored during training at each update cycle. 

We use [*Rectified Linear Units*](https://en.wikipedia.org/wiki/Rectifier_(neural_networks)) (ReLU) activations for the hidden layers as they are the simplest non-linear activation functions available.

For multi-class classification, we may want to convert the units outputs to probabilities, which can be done using the *softmax* function. We decide to use the *categorical cross-entropy* loss function.
Finally, we choose [Adam optimizer](https://arxiv.org/abs/1412.6980) as it seems to be well suited to classification tasks. 

```python
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation

def build_model(input_dim, hidden_neurons, output_dim):
    """
    Construct, compile and return a Keras model which will be used to fit/predict
    """
    model = Sequential([
        Dense(hidden_neurons, input_dim=input_dim),
        Activation('relu'),
        Dropout(0.2),
        Dense(hidden_neurons),
        Activation('relu'),
        Dropout(0.2),
        Dense(output_dim, activation='softmax')
    ])
    
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model
``` 


### Creating a wrapper between Keras API and Scikit-Learn

[`Keras`](https://github.com/fchollet/keras/) provides a wrapper called [`KerasClassifier`](https://keras.io/scikit-learn-api/) which implements the [Scikit-Learn](http://scikit-learn.org/stable/) classifier interface. 

All model parameters are defined below.
We need to provide a function that returns the structure of a neural network (`build_fn`). 
The number of hidden neurons and the batch size are choose quite arbitrarily. We set the number of epochs to 5 because with more iterations the Multilayer Perceptron starts overfitting (even with [Dropout Regularization](https://arxiv.org/abs/1207.0580)). 

```python
from keras.wrappers.scikit_learn import KerasClassifier

model_params = {
    'build_fn': build_model,
    'input_dim': X_train.shape[1],
    'hidden_neurons': 512,
    'output_dim': y_train.shape[1],
    'epochs': 5,
    'batch_size': 256,
    'verbose': 1,
    'validation_data': (X_val, y_val),
    'shuffle': True
}

clf = KerasClassifier(**model_params)
```

### Training our Keras model
Finally, we can train our Multilayer perceptron on train dataset.
```python
hist = clf.fit(X_train, y_train)
```

With the callback history provided we can visualize the model *log loss* and *accuracy* against time.

```python
import matplotlib.pyplot as plt

def plot_model_performance(train_loss, train_acc, train_val_loss, train_val_acc):
    """ Plot model loss and accuracy through epochs. """

    green = '#72C29B'
    orange = '#FFA577'

    with plt.xkcd():
        # plot model loss
        fig, ax1 = plt.subplots()
        ax1.plot(range(1, len(train_loss) + 1), train_loss, green, linewidth=5,
                 label='training')
        ax1.plot(range(1, len(train_val_loss) + 1), train_val_loss, orange,
                 linewidth=5, label='validation')
        ax1.set_xlabel('# epoch')
        ax1.set_ylabel('loss')
        ax1.tick_params('y')
        ax1.legend(loc='upper right', shadow=False)
        # plot model accuracy
        fig, ax2 = plt.subplots()
        ax2.plot(range(1, len(train_acc) + 1), train_acc, green, linewidth=5,
                 label='training')
        ax2.plot(range(1, len(train_val_acc) + 1), train_val_acc, orange,
                 linewidth=5, label='validation')
        ax2.set_xlabel('# epoch')
        ax2.set_ylabel('accuracy')
        ax2.tick_params('y')
        ax2.legend(loc='lower right', shadow=False)
```

```python
# Plot model performance
plot_model_performance(
    train_loss=hist.history.get('loss', []),
    train_acc=hist.history.get('acc', []),
    train_val_loss=hist.history.get('val_loss', []),
    train_val_acc=hist.history.get('val_acc', [])
)
```

<div align="center">
  <img src="{{ site.baseurl }}/assets/images/DataScience/pos_tagging_neural_nets_keras/loss.png" alt="loss"/>
</div>

<div align="center">
  <img src="{{ site.baseurl }}/assets/images/DataScience/pos_tagging_neural_nets_keras/accuracy.png" alt="accuracy"/>
</div>

After 2 epochs, we see that our model begins to overfit. 

### Evaluating our Multilayer Perceptron

Since our model is trained, we can evaluate it (compute its accuracy):
```python
score = clf.score(X_test, y_test)
print(score)
```

```python
0.95816
```

We are pretty close to 96% accuracy on test dataset, that is quite impressive when you look at the basic features we injected in the model.
Keep also in mind that 100% accuracy is not possible even for human annotators. We estimate humans can do Part-of-Speech tagging at about 98% accuracy.

### Visualizing the model

```python
from keras.utils import plot_model
plot_model(clf.model, to_file='model.png', show_shapes=True)
```

<div align="center">
  <img src="{{ site.baseurl }}/assets/images/DataScience/pos_tagging_neural_nets_keras/model.png" alt="model"/>
</div>

### Save the Keras model

Saving a Keras model is pretty simple as a method is provided natively:
```python
clf.model.save('/tmp/keras_mlp.h5')
```
This saves the architecture of the model, the weights as well as the training configuration (loss, optimizer).


### Ressources

- _`Keras`: The Python Deep Learning library_: [[doc]](https://keras.io/)  
- _Adam: A Method for Stochastic Optimization_: [[paper]](https://arxiv.org/abs/1412.6980)  
- _Improving neural networks by preventing co-adaptation of feature detectors_: [[paper]](https://arxiv.org/abs/1207.0580)  

In this post, you learn how to define and evaluate accuracy of a neural network for multi-class classification using the Keras library.  
The script used to illustrate this post is provided here : [[.py](https://github.com/Cdiscount/IT-Blog/blob/master/samples/DataScience/pos-tagging-neural-nets-keras/pos_tagging_neural_nets_keras.py)|[.ipynb](https://github.com/Cdiscount/IT-Blog/blob/master/samples/DataScience/pos-tagging-neural-nets-keras/pos_tagging_neural_nets_keras.ipynb)].
