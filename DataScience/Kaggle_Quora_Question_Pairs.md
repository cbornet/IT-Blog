# Our participation to the Kaggle challenge: Quora Question Pairs

_Bruno Goutorbe_<br>
_Chief Data Scientist at Cdiscount_

So, we decided to spend a little of our time on a Kaggle challenge, 
namely, [_Quora Question Pairs_](https://www.kaggle.com/c/quora-question-pairs).
(By "we", I mean the data scientists of Cdiscount.) 
The purpose of the
challenge consisted in detecting duplicate questions, that is, pairs 
of questions carrying the same meaning. This is of interest
to us, as we work on loosely related issues: for exemple, 
we need to detect algorithmically duplicate products in our catalog
(which contains more than 20 million active items) or to match them
against competitors' catalogs.

The challenge took place from March 16<sup>th</sup> to June 
6<sup>th</sup>, 2017. We came around quite late, 
about one month after it started, so we mostly ran after the score and
finished in the top 8%. Here:
 
![](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/kaggle-quora-final-ranking.png "Final ranking")

## The challenge

As its name indicates, the challenge was organized by the 
question-and-answer website, [Quora](https://www.quora.com/).
The objective consisted in submitting the best machine learning model
capable of predicting whether two questions are duplicates of each other,
or not. In order to train the models, Quora released a set of more than
400,000 pairs or questions with a label: duplicate or not duplicate.

### Training set

See some examples of questions that are _not_ duplicates (about 60% of the set):

question 1 | question 2 | is_duplicate
-----------|------------|------------
What is the step by step guide to invest in share market in india? | What is the step by step guide to invest in share market? | 0
How can I increase the speed of my internet connection while using a VPN? | How can Internet speed be increased by hacking through DNS? | 0
Which one dissolve in water quikly sugar, salt, methane and carbon dioxide? | Which fish would survive in salt water? | 0

And some examples of duplicates (about 40% of the set):

question 1 | question 2 | is_duplicate
-----------|------------|------------
How can I be a good geologist? | What should I do to be a great geologist? | 1
How do I read and find my YouTube comments? | How can I see all my Youtube comments? | 1
What can make Physics easy to learn? | How can you make physics easy to learn? | 1

### Testing set

As for the testing set, it contains more than 2,3 millions pairs of 
questions. Have a look:

question 1 | question 2
-----------|-----------
How does the Surface Pro himself 4 compare with iPad Pro? | Why did Microsoft choose core m3 and not core i3 home Surface Pro 4?
What but is the best way to send money from China to the US? | What you send money to China?
How "aberystwyth" start reading? | How their can I start reading?

Uh? Many questions don't seem to make sense at all, but
we'll come back to it later.

### Evaluation metric

For each pair of the testing set, the submitted model is expected to
predict a probability of the questions to be duplicates.
Quora chose the [logistic loss](http://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html)
metric to evaluate the quality of the predictions. In short, this metric
strongly penalizes models that are confident about an incorrect
classification.

## Lessons

### Feature enginering

Feature construction was the core ingredient of the challenge. The participants
(including ourselves) built a wide variety of input variables, which generally 
included:
- Simple statistics, such as the length (and difference in lengths) of the 
pairs of questions;
- Similarities between the pairs based on the characters constituting the questions,
such as Levenshtein and related similarities used in fuzzy string matching;
- Similarities between the pairs based on the set of words constituting the 
questions, such as the Jaccard index;
- Various distances (L1, L2, cosine, canberra...) between vector representations
of the questions derived from TF-IDF statistics and pre-trained Word2Vec models 
(Google News, Glove, FastText);
- Presence of important words such a _why, when_... in the questions.

This is obviously a time-consuming task which was performed incrementally. 
By the end of the challenge we came up with about a hundred features. This is
somewhat far from the best-ranked submissions, which, according to what we
read in the discussion forum, reached several hundreds of features.

Interestingly, some of our data scientists adopted a more "brute-force" approach
which consisted in defining one feature per word of the corpus taking on the
value of 
- 0: word present in none of the questions, 
- 1: word present in only one question, 
- or 2: word present in both questions.

In other words the features corresponded to a sum of binary TF applied to the
questions. This approach had the advantage of moving part of the effort of
identifying discriminating words or combinations of words to the (training phase
of the) models. The inconvenient being that it led to over-bloated models,
e.g., xgboost models with tens of thousands of trees taking the whole night
to train.
  
### Leaky features

During the feature engineering phase, participants soon identified
[_leaky features_](https://www.kaggle.com/wiki/Leakage), that is, highly
predictive variables related to biases in the way the testing set was built
rather than real relationships with respect to the property to predict, thus
useless in a real-world application. Two such features surfaced in the discussion
forum:

- the total number of occurences of each question, within __both__ 
the training and testing sets;

- the number of common neighbours between each pair of questions:
neighbours are defined as questions appearing together in a
pair, __either in the training set or in the testing set, be they
labelled as duplicates or not__.

These two leaking features allow decreasing the score by about 0.1:
this is a huge improvement, if you look at the top figure showing
the final rank vs. score. We suspect that the best ranked submissions
found and exploited more leaks in the data sets. These leaks could
be related to the way questions were selected in the sets (e.g.,
questions having at least one identified duplicate may have been
oversampled); or to the [computer-generated questions included
in the testing set](https://www.kaggle.com/c/quora-question-pairs/data)
as anti-cheating measure (remember, those silly questions
we spotted above?).

In any case, these leaks should remind data science teams willing
to organize Kaggle-like challenges that great caution should be
exercised in preparing the data sets.
  
### Models

This challenge confirmed the 
[Extreme Gradient Boosting](http://xgboost.readthedocs.io/en/latest/)
model (xgboost) as an indispensable method for anyone willing to obtain a 
decent score within a Kaggle competition. We all ended up resorting
to xgboost, like the vast majority of the participants if we believe
the discussion forum. In addition, neural networks also seem to
have played an essential part in the top contributions.
Unfortunately, we have not spent much effort optimizing such models 
due to lack of time.
  
### Rebalancing

Duplicates make around 40% of the training set, and an estimated
15-20% of the testing set. Rebalancing the former set before
training the models allowed to improve the score y about 10%.

### Model ensembling

By the end of the challenge, we merged the models we had been
building seperately until then, which significantly boosted 
our score. Model ensembling is an efficient technique which is
well-known to Kagglers, but it is still fascinating to observe
it in practice. A simple averaging of the predictions improved
the overall score by about 10%. Using another xgboost on top
of the individual models, which took the individual predictions
as input features, allowed us to reduce the score even more.
(To do this we had to set aside a part of the training set,
train the base models on the remaning part and use the predictions
on the subset left aside as input features to train the
top layer xgboost.)

This raised hopes for further
improvements by adding additional features alongside the
predictions of the base layer models: we hoped that the top layer
xgboost could thence identify in which areas of the features space
each of the base models performed better, in order to fine-tune
the aggregation. Much to our disappointment, this approach did not
yield any improvement of the score despite our various attempts:
addition of all features, of top features, of random features,
of PCA-reduced features...

## Conclusion

Participating to a Kaggle challenge proved to be a rich experience,
which allowed our data scientists to push machine learning 
approaches to their limits. Think about model ensembling for
example: this is not something we normally do in a production
environment, so we learnt a lot by putting this in practice.

We hope we can clear some time again in a few months to participate
to another challenge. Three things we will then do better: (1)
start on time; (2) use neural networks; (3) master model ensembling
with additional features.

See you soon!