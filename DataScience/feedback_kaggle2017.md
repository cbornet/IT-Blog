# A quick experience feedback about the Cdiscount image classification Kaggle competition

_Julien Jouganous, Data Scientist at Cdiscount_


## Introduction: 
Three months ago, we launched a data science competition on the famous [Kaggle](https://www.kaggle.com/) platform. The aim was to develop a product classifier based on image analysis. Indeed, our catalog is made up of more than 30 million products. Making sure they are all well classified is very challenging as well as crucial given that numerous critical algorithms (search engine ranking, product recommendation, *etc*) rely on product categorization.
So far we applied text mining techniques to the text descriptions of the products to predict their category. A previous [challenge](https://www.datascience.net/fr/home/) hosted on the French platform [**datascience.net**](https://www.datascience.net/fr/challenge/20/details) was dedicated to this approach. Nonetheless, we were convinced that a substantial uplift could be reached by integrating images in the pipeline.

The data set provided for the challenge contains more than 15 million images of about 9 million products (_i.e_ almost half of our current catalog), making it one of the largest public database of labelled images. These products are divided into more than 5000 categories, which makes this challenge an **extreme multimodal classification problem**. The winners of the contest will share a $35,000 prize.

The challenge concluded a few days ago (on December 14, 2017) and promises were kept! More than 750 competitors (distributed into 627 teams) took part in the challenge, among which some of the most talented data scientists and deep learning experts around the world.

**Figure 1** shows the evolution

Results are very impressive as the winner *bestfitting* (currently No.1 at kaggle global ranking) reached **79.6%** accuracy on the private leaderboard and more than 120 competitors overcame 70% of correct categorization (see **Figure 2** below).

![timeline](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/feedback_kaggle/kpi_evol.PNG "Figure 1: Evolution of top accuracy and number of teams involved")

![Figure 2](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/feedback_kaggle/scores.png "Figure 2: scores distribution") 

## Strategies used:

You can get a good overview of the different machine learning algorithms used by the competitors looking at the dedicated [Discussion section](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion) on Kaggle or reading the [winner's post](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45863). We were able to identify some key success factors which are described below.

#### Deep learning rocks!
Even if interesting performances could be reached by traditional ML algorithms (see [baseline submission](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/39463) for instance), a vast majority of the top ranked solutions involve deep neural networks.
The usual python implementations (TensorFlow, Keras, PyTorch) were in the game and the best results were obtained by finetuning well known pretrained deep (convolutional) neural nets such as the different architectures of ResNet, Inception-ResNet, DenseNet...

#### Ensembling methods to climb the last percents of the accuracy curve
Strength lies in unity, and ensembling methods built on top of several neural nets allowed to combine the power of the different models, thus improving significantly the accuracy.

In [this topic](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45733), the authors explain how they gathered outputs from several CNNs. Each individual model has a respectable accuracy (about **74-75%**) but combining them, even by simply average leads to a **77.5%** score. Adding a multi-layer ensembling algorithm (based on classical ML techniques such as XGBoost, Random Forest and other variants) further improves the accuracy of the pipeline (**78.7%**).

Similarly, numerous efficient solutions were obtained by teams of up to five data scientists merging their individual models andshowing the strength of the Kaggle community.

#### Other tricks that make the difference
Most of the top 20 competitors or teams applied ensembling methods over finetuned CNNs. How to stand out and get the small plus that makes you win the competition?

Different tricks were found by competitors to finetune models or prepare data, some of which are described below. 

A particularity of the data set is that we provided up to 4 pictures per product. Using only the first one is often enough to find the category but in some difficult cases combining the distinct images of the product can help. Consequently, several competitors used combinations or concatenations of the pictures to improve their models. For instance, the winner (see his solution [here](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45863)) concatenated images of the same product into one single "mozaic" picture. Then he designed separated models for products with 1, 2, 3 or 4 pictures.

Examples are provided below:

![Figure 3](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/feedback_kaggle/1st_img_better_480.png "Figure 3: the first picture seems informative enough.")

![Figure 4](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/feedback_kaggle/differents_angles.png "Figure 4: all pictures are informative.")

![Figure 5](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/DataScience/feedback_kaggle/differents_envs.png "Figure 5: the first image doesn't seem the easiest to deal with because of the background.")

In the top raw (**Figure 3**), the first image seems to be the most relevant to predict the category. In the middle case (**Figure 4**), pictures are taken under distinct angles so we can believe that they are all informative. In the last raw (**Figure 5**), the first picture presents the item within its background which can make the classification task harder. Conversely the second one seems easier to process as there is no background. In the last two cases, using the whole set of images is probably more efficient than dealing with only one picture.

Another clever key feature of the winner's solution is to use an optical character recognition (OCR) algorithm to extract text from the pictures. Indeed, he noticed that for some categories of products, such as CDs or books, the shape is not super informative whereas the text appearing in the pictures can potentially help.

If you are interested in more detailed insights on the algorithms and tricks used by the competitors you'll find interesting topics in the [discussion channel](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion). 

#### High performance hardware configurations
It is well known that training deep learning methods is very computationally expensive, especially when dealing with huge amounts of pictures. This competition and the discussions about hardware (see [this topic](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45724)) give a good overview of the state of the art setups. The key finding, as you may expect, is that you need (powerful) GPUs. And the more, the better! Common hardwares are composed for instance of up to four 1080ti or Titan GPUs generally combined with 64Gb RAM and SSD storage.


## Conclusion
The competition is a great success for Cdiscount as we could reach impressive categorization rates and learn a lot from the winning solutions. Kaggle community showed its efficiency to address such a complicated problem, taking benefit from the emulation and the mutual assistance between its brilliant members. 
We hope that such a large labelled image dataset has the potential to contribute to deep learning improvements thanks to the amount of pictures now available and the large number of classes.

We will now test in real conditions the winning algorithms and combine it to our current text based categorization algorithm to improve our pipeline.

Thanks again to Kaggle and all the competitors who, thanks to their time, efforts and talent, had make it a success!

See you soon!


## References

#### A few links:

* [the previous challenge](https://www.datascience.net/fr/challenge/20/details) on text based classification on **datascience.net**,
* Cdiscount Kaggle challenge [homepage](https://www.kaggle.com/c/cdiscount-image-classification-challenge),
* the [discussion channel](https://www.kaggle.com/c/cdiscount-image-classification-challenge).

#### Some interesting topics:
* the winning [solution](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45863),
* an efficient [single model solution](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45850),
* a few other top ranked algorithms: [here](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45733),
[here](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45709) or 
[there](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45737),
* [hardware configurations](https://www.kaggle.com/c/cdiscount-image-classification-challenge/discussion/45724).
