
# A brief overview of Automatic Machine Learning solutions (AutoML)

## What is AutoML and why do we need it?
Auto ML is the fact of simplifying data science projects by automating the machine learning tasks. The figure below presents a classical machine learning pipeline for supervised learning tasks.

![Machine learning process](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/ML_process.PNG "Figure 1: A machine learning process.")

In the process presented above, several blocks have to be tuned to extract most of the predictive power of the data: 
* First of all, you have to select relevant data that potentially explain the target you want to predict.
* Once these raw data are extracted, you generally need to process them. A non-exhausive list of preprocessing steps is given below:
    * text vectorization
    * categorical data encoding (one hot...)
    * missing values and outliers processing
    * rescaling (normalization, standardization, min-max scaling...)
    * variables discretization
    * dimensionality reduction
    * ...
* Last but not least, you have to choose a machine learning algorithm depending on the kind of task you are facing: supervised or not, classification or regression, online or batch learning... 

Most machine learning algorithms need parameterization and even if some empirical strategies can help ([this article](https://www.analyticsvidhya.com/blog/2016/03/complete-guide-parameter-tuning-xgboost-with-codes-python/) provides guidelines for [XGBoost](http://xgboost.readthedocs.io/en/latest/)), this optimization is complex and there is generally no deterministic way to find the optimal solution. But that is only the tip of the iceberg as the whole process involves choices and manual interventions that will impact the efficiency of the machine learning pipeline.

### Welcome to the hyperparameters jungle!
To illustrate this, consider the classical __spam detection problem__: using the content of emails, you want to predict whether an email is a spam or not. To do that, we have a database with emails tagged as SPAM or NOT_SPAM so this is a supervised binary classification problem.

![Spam detection](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/spam.PNG "Figure 2: Spam detection.")

As machine learning algorithms generally deal with numerical vectors, the first step is to vectorize our emails. We can use a [tf-idf](http://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting) approach. But before, we have to tokenize the emails (turn sentences into lists of words). We may also want to apply more advanced text preprocessing such as lowercasing, [stemming, lemmatization](https://nlp.stanford.edu/IR-book/html/htmledition/stemming-and-lemmatization-1.html), or spelling correction. 

Now the emails are tokenized and preprocessed, we can vectorize it computing the tf-idf weights but here again the algorithm needs to be parameterized. Indeed, we generally want to specify stopwords, truncate the document frequency range (*i.e.* remove from the dictionnary rare and/or frequent words), or even include *n-grams* (sequences of *n* consecutive words) into our dictionnary.

We have a vectorized representation of our emails. We may or may not want to apply a dimensionality reduction technique such as PCA. We may also want to add other features such as the number of words in the mail, the average word length...

It is now time to train our machine learning model but which one will we use?

For this kind of batch supervised binary classification task, we are spoilt for choice: logistic regression, naive Bayes classifier, random forest, gradient boosting, neural nets... We probably want to try and compare some of these algorithms but here let say that we have chosen the __random forest__. How many decision trees do we need? What is the optimal tree depth? How do we control the leaves granularity? How many samples and features do we want to include in each tree? 

Just have a look at the [scikit learn documentation](http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html) to have an overview of the amount of hyperparameters you can tune. 

Finally, each component of the pipeline involves choices and parameters that can impact the performances of the algorithm. Auto ML simply consists in automating all these steps and optimizing data preprocessing, algorithm choice and hyperparameters tuning.

## Hyperparameters optimization strategies
### Mathematical formalism 
Consider ![eq1](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq1.svg) the possible strategies space. It may sound a bit abstract but let's just say that each element ![eq2](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq2.svg) is a parameterization of the machine learning pipeline from the data processing to the model hyperparameters tuning. The auto ML process aims at finding ![eq3](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq3.svg) such that: 

![eq4](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq4.svg)

where ![eq5](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq5.svg) and ![eq6](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq6.svg) are train and validation sets obtained via _K-fold_ cross validation and ![eq7](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq7.svg) is the loss value for pipeline ![eq8](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq8.svg) trained on ![eq9](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq9.svg) and evaluated on ![eq10](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq10.svg).


Finally it looks like a **classical optimization problem**. 
There is no reason the function to minimize is convex so gradient based optimization techniques are not likely to be efficient. 
A few strategies that can be used in this case are briefly described below.

### Random search, grid search
The first and simplest tuning approach that may come to mind is just picking randomly several parameterizations of the pipeline and keep the best one. A variant called grid search consists in testing the nodes of a discretization grid of ![eq1](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq1.svg). 
For more details, these algorithms are implemented in scikit learn, [here](http://scikit-learn.org/stable/modules/grid_search.html) is the documentation.

These Monte-Carlo-like algorithms can be a good starting point for low dimensional problems but, as we saw before, we generally have a consequent amount of parameters to tweak so they will converge very slowly. Moreover, in the grid search case, if optimal strategies are far from the nodes you defined, you have no chance to discover them.

### Metaheuristics
To overcome the poor convergence properties of random search, one may want to implement more "clever" algorithms. Metaheuristics are a class of generic optimization techniques based on the exploitation  / exploration trade-off and often mimicking biological or physical phenomena. They can be efficient to solve convex and non-convex problems. 

Among the tons of metaheuristics, we can mention for instance:

* **Simulated annealing** is a method inspired from annealing in metallurgy that consists in alternating cooling and heating phases to minimize the material enregy modifying its micro structure and physical properties. In analogy, we explore the parameters space to try to minimize the system energy (our objective function). We also introduce the temperature of the material *T*. At each step, we test a configuration in the neighborhood of the previous one. The higher the temperature is, the more the atoms are free to move and the larger the neighborhood is. Consequently, at the beginning of the process, when *T* is high, we explore pretty much all the search space and as this temperature decreases, we focus more and more on the areas deemed promising.
See [here](http://katrinaeg.com/simulated-annealing.html) for a more detailled description.


* **Particle swarms** uses a population of candidate solutions (or particles) to explore the space ![eq1](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq1.svg). Each particle moves in ![eq1](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq1.svg) depending on its current location, its best known past position and the whole population's best position. The trade-off between exploitation and exploration can be tuned by playing whith the relative importance of these different factors. [This paper](http://bee22.com/resources/Poli%202007.pdf) gives more details about the algorithm and some variants.

* **Evolutionary algorithms** is a family of algorithms inspired by biological evolution. We consider a population of candidate solutions (or individuals) and we apply simplified evolution laws to have them optimize the objective function called **fitness**. At each step or generation, we select the best (meaning here the fittest) individuals. The next generation is built via the reproduction of these selected individuals. During this step we apply genetic operations: **recombination** (exploitation) is the process by which the parents features are combined to form children solutions, whereas **mutations**, introduce random (exploration) perturbations. This way, the average population's fitness is supposed to improve from one generation to the next and the fittest individual to converge to a good solution of your optimization problem.

### Bayesian approaches  
Each evaluation of the objective function we try to minimize can be very expensive as we have to train and evaluate a machine learning pipeline. Bayesian optimization provides an efficient method to explore the parameter set and converge quickly to a convenient solution. In short: it helps focus the exploration of the parameter space ![eq1](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/eq1.svg) on promising areas. The Figure below ([source](http://haikufactory.com/files/bayopt.pdf)) gives a simple example in one dimension (in this case, we want to maximize the function):

![Bayesian optimization](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/img_bayesian_opt.PNG "Figure 3: Bayesian optimization.")

In this example, the objective function *f* is approximated through a [Gaussian Process regression](http://mlg.eng.cam.ac.uk/zoubin/papers/aistats07localGP.pdf) model. This modelling technique provides a probability density function for the values of *f* based on priors (points where the value of the function is known). This density is represented by the blue area and the mean is plotted in solid line. The distribution is very peaked (small variance) close to observations whereas we are not confident (high variance) with our estimations of *f* in unsampled areas.

At each step, the new point to explore is selected as the maximum of a function called **activation function** (the green one). This function synthesizes the *a priori* knowledge and the uncertainty about the function to optimize. It is high where the predicted objective function is high (or low if we want to minimize *f*) and where the uncertainty is also high. In other words, it is high where there is a good chance we find better solutions for our optimization problem.


## The opposing forces
In this section we provide a non exhaustive list of auto ML solutions currently available. We arbitrarily chose a few summary features to compare them: Is it a open source package? Which backend models implementation and hyperparameters tuning algorithms are used? How many contributors?

These features, when they where available, were gathered in the table below. Note that it is a snapshot of these libraries at the time this article was written.

Solution | Open source| Nb of contributors | Backend models | Optimization algorithms | Other features 
-----------|------------|------------|-----------
[_Amazon AWS Machine learning_](https://aws.amazon.com/fr/machine-learning/) | No | -  | TensorFlow, PyTorch... | - | cloud, access to GPUs, can be combined with other tools (data storage, querying...)
[_Autosklearn_](https://github.com/automl/auto-sklearn) | Yes | 25 | sklearn | bayesian | -
[_AutoWeka_](https://github.com/automl/autoweka) | Yes | 4 | java WEKA ml library | bayesian, grid search | -
[_DataRobot_](https://www.datarobot.com/product/) | No | - | - | - | handles deployment, cloud
[_Google Cloud HyperTune_](https://cloud.google.com/ml-engine/docs/tensorflow/hyperparameter-tuning-overview) | No | - | Tensorflow | bayesian | cloud, data exploration and preparation through Google Cloud Datalab
[_H2O_](https://h2o-release.s3.amazonaws.com/h2o/rel-turan/4/docs-website/h2o-py/docs/intro.html) | Yes | 102 | H2O | grid search | can be distributed
[_H2O Driverless_](http://docs.h2o.ai/driverless-ai/latest-stable/docs/userguide/index.html) | No | - | H2O | - | performs features engineering
[_Hyperopt_](https://github.com/hyperopt/hyperopt) | Yes | 25 | - | random, tree parzen estimator | -
[_IBM Watson_](https://www.ibm.com/watson/) | No | - | - | - | -
[_MLBox_](https://github.com/AxeldeRomblay/MLBox) | Yes | 3 | sklearn, keras, xgboost... | tree parzen estimator | basic data pre-processing, feature selection
[_PyBrain_](http://pybrain.org/docs/) | Yes | 32 | homemade + libraries (LIBSVM) | metaheuristics, grid search... | -
[_TPOT_](http://epistasislab.github.io/tpot/) | Yes | 32 | sklearn | genetic | -

We could play with a few of these auto ML solutions. Our tests are summarized in the following section.

## Benchmark
### Protocol
We chose four frameworks to test. The main selection criteria where the diversity and community involved (number of contributors, recency of the last commit).
* AWS Machine Learning (version available on 2017/12/05)
* Autosklearn 0.2.0
* H2O 3.16
* TPOT 0.9.1

These packages were benchmarked on three classical datasets available on [Kaggle](https://www.kaggle.com/): 
* A **binary classification** problem: [Titanic survival prediction](https://www.kaggle.com/c/titanic)
* A **multiclass classification** challenge: [Digit recognizer](https://www.kaggle.com/c/digit-recognizer) based on the MNIST dataset
* A **regression** problem: [House prices](https://www.kaggle.com/c/house-prices-advanced-regression-techniques)

This way, we can compare the results to the general leaderboards (and an army of talented data scientists) on different kinds of supervized learning problems.

We trained each solution on the training set during **1 hour** on **32 cores - 256Go RAM** server and then submitted the predictions on the test set on Kaggle. The results are provided in the figures below.

### Results
For each challenge, we plotted the metric value depending on the ranking of the solution for the whole leaderboard and located the libraries we tested on these plots. Basic baseline solutions are also provided.

**Titanic challenge (binary classification):**
* metric: *accuracy* (percentage of correctly predicted labels)
* number of challengers: 11164 teams (11700 competitors)
* number of features: 9
* number of samples: 891 in the training set, 418 in the test set
* baseline: predictions based on gender (men die and women survive)

![Titanic challenge benchmark](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/bench_titanic_graph.png "Figure 4: Titanic challenge benchmark.")

This curve shows for instance that the top 20% solutions reached more than 80% accuracy.

**MNIST (multiclass classification):**
* metric: *accuracy*
* number of challengers: 2288 teams (2345 contributors)
* number of features: 784
* number of samples: 42000 in the training set, 28000 in the test set
* baseline: k nearest neighbors with k=1

![MNIST challenge benchmark](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/bench_mnist_graph.png "Figure 5: MNIST challenge benchmark.")

**House prices (regression):**
* metric: *root mean squared error (RMSE)*
* number of challengers: 5123 teams (5397 competitors)
* number of features: 268
* number of samples: 1460 in the training set, 1459 in the test set
* baseline: linear regression (area, number of bedrooms, year and month of sale)

![House prices challenge benchmark](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/automl/bench_house_price_graph.png "Figure 6: House prices challenge benchmark.")

## Conclusion
In practice, the open source frameworks needed some data preparation and cleaning (binarization, null values handling...). Only commercial solutions offer the complete pipeline, from features engineering to models deployment.

Moreover, hyperparameters tuning algorithms sometimes need to be parameterized. It is for instance the case for the genetic algorithm used by TPOT.

Open source Auto ML solutions does not perform better than human data scientists (top 20-80% on the leaderboard depending on the challenge) but can help get convenient levels of accuracy with a minimum effort and amount of time.

Keep in mind that feature engineering is the key : "one of the holy grails of machine learning is to automate more and more of the feature engineering process" ([Pedro Domingos, _A Few Useful Things to Know about Machine Learning_](https://bit.ly/things_to_know_ml)). 
This is where most of the effort in a machine learning project goes because it is a very time-consuming task.


## Further readings
* [about particle swarms optimization](http://bee22.com/resources/Poli%202007.pdf)
* [about simulated annealing](http://katrinaeg.com/simulated-annealing.html)
* [about bayesian optimization](http://haikufactory.com/files/bayopt.pdf)