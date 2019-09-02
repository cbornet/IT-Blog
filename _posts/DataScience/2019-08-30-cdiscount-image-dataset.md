---
layout: post
title:  "Cdiscount image dataset for visual search and product classification"
author: datascience.team
categories: [ en, data science ]
image: "assets/images/DataScience/cdiscount_image_dataset/banner.jpg"
mathjax: true
---

> 12M images of 7M products classified into 5K categories


## Images from a large e-retailer

Recent advances in artificial intelligence and image recognition allow a whole new set of services to improve the Internet shopping experience. Among those new services, visual search is probably one of the most promising technique as it provides an effective and natural way to search through a catalog with a simple picture.

Improving visual recommendation algorithms requires access to large labeled image datasets, possibly specialized in the core business they address. Available generic image datasets include 
[_TinyImage_](https://groups.csail.mit.edu/vision/TinyImages/), [_LabelMe_](http://labelme.csail.mit.edu/Release3.0/browserTools/php/dataset.php), [_Lotus Hill_](https://ieeexplore.ieee.org/document/5204331), 
Microsoft [_Common Objects in Context_ (_COCO_)](http://cocodataset.org/#home) or [_OpenImages_](https://github.com/openimages/dataset). Of course, [_ImageNet_](http://www.image-net.org/) is the _de facto_ standard to bench image classification algorithms involving extremely large numbers of labels.

Most of the public datasets that are of direct use to on-line retailers are specialized in fashion items: the [_Exact Street2Shop_](http://www.tamaraberg.com/street2shop/wheretobuyit/README.txt) dataset identifies around 40,000 clothing items worn by 
people on real-world street photos, and provides their exact match amongst hundreds of thousands of images from shopping websites; [_DeepFashion_](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html) consists of over 800,000 annotated images that 
contain clothes. 

To the best of our knowledge, no comprehensive image dataset covering products typically sold by generalist retailers is yet available to the community. This is the reason why we are releasing a large dataset of such categorized product images. With more than 12M images of 7M products classified into 5270 categories, this dataset should help the community to leverage state-of-the-art neural network architectures in order to develop better recommendation systems.

In the following article, we present several aspects of the dataset such as the way it was build and organized or some specific features that you might want to consider before training a model on it. We also get a grasp of the approaches followed by the 3 winning teams of the Kaggle competition we organized on this dataset.

The full dataset can be downloaded from the Kaggle platform at the following address: [kaggle.com/c/cdiscount-image-classification-challenge](https://www.kaggle.com/c/cdiscount-image-classification-challenge)

## Structure of the Cdiscount dataset

Our image dataset has been extracted from the full list of more than 40M products available at 
[__*cdiscount.com*__](https://cdiscount.com) in July, 2017. 

Products are coming from our own list of products or from our Market Place where independent resellers can put their products up for sell. Our own catalog being rich of approximately 200,000 products, the vast majority of the 7M products in the dataset originates from the nearly 10,000 independent resellers present on our Market Place.

The dataset is organized according to a 3-level classification tree with categories labeled in French. 


The 1st level of aggregation is referred to as Cat I for Category level I and contains a diversity of products that could be compared to a physical store, like a drugstore or a wine shop. 
It is the most generic level of aggregation and as such is of particular interest if one wishes to focus on a particular subset of images such as CHILDCARE (PUERICULTURE), BAGS (BAGAGERIE) or INTERIOR DESIGN (DECORATION). 
The 49 distinct Cat I categories are listed in table 1 with the corresponding English translation. 

![table_1]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/table1.png)

The 2nd level category (Cat II) is of lesser importance. 
It is an intermediate step before the 3rd and most specific level which gathers identical products or objects. Examples of these 3rd level categories (Cat III) belonging to the 3 stores mentioned above would be BABY BOTTLE (BIBERON), TRAVEL BAG (SAC DE VOYAGE) and PHOTO FRAME (CADRE PHOTO). 

The number of categories for each level is given in table 2. A ratio of roughly 1 to 10 is observed in the number of categories from one level to the next, leading to 5270 distinct Cat III categories. It is worth noting that there are actually 5263 distinct values taken by the 5270 Cat III categories: 7 couples of them share the same name while belonging to different Cat II categories. However, the combination Cat II & Cat III is uniquely defined through the dataset. Finally, each of the 5270 Cat I & Cat II & Cat III category is encoded with an integer index in the dataset.

![table_2]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/table2.png)

Down to the level of products, we count between 1 and 4 180x180 pixel images that can be associated to a given product. 
There aren’t any specific rule to define that number as within our Market Place, a reseller is simply given the choice to insert 1, 2, 3 or 4 images with his product. 

![table_3]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/table3.png)

Table 3 summarizes the distribution of products according to the number of associated images. More than half the number of products have only 1 image. Those images represent 1/3 of the total number of images in the dataset. Finally, we count precisely 12,371,293 images for 7,069,896 products.

## Labelled images of products

The labelling of this dataset was made using textual descriptions of each product in our catalog.
 The process of classification is semi-automatized: a [K-NN](https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm) is applied to classify every product
  and if the required confidence level isn’t met for a given product, it is sent to manual classification. Finally, the overall quality of the classification is assessed by frequent sampling operations in which a trained expert is asked to visually control the classification.

The measured overall rate of bad classification based on this sampling technique is around 10 % in each category. This number gives the order of magnitude of noise associated with our image dataset.

![figure_1]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/figure1.png)

Figure 1 shows illustrative examples of images that can be found in the dataset. Background may vary from one image to the other. A product might be presented on a white or colored background or might be shown in an illustrative situation like the wall decoration or the dresser. Images might be views of the same object with different angles like for the helmet or they might be showing a zoom on some specific detail of the product as for the couch. The product may also be represented more than once like the watch. 

Finally, for some specific products, one of the images might not be showing the product at all. This is the case for the fridge as, according to the European Union regulation, electrical goods all have to carry an EU energy label.

## Unbalanced categories

Our product catalog is highly diverse and the categorization tree we use is not aimed at balancing the number of products among the categories. It is rather aimed at gathering products with similar characteristics and purposes. This results in a highly unbalanced number of products per categories.

![figure_2]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/figure2.png)

Figure 2 shows 3 distributions of products per category, one for each hierarchical level of category. It should be noted that the bin widths used to draw these histograms vary on a logarithmic scale to facilitate the visualization of several orders of magnitude on the same plot.

At the Cat I level, the spread is considerable. There is a small cluster of 5 categories with less than 200 products (APICULTURE, PRODUITS SURGELES, ABONNEMENTS/SERVICES, PRODUITS FRAIS, FUNERAIRE). The rest of the 44 categories gather between roughly 104 and 106 products each. The last bin alone contains 9 categories in which 4.5M products (more than half the products) are to be found in total.

At the Cat II level, the spread remains important. It varies between 10 and half a million of products in just one category named PARTS (PIECES). The mode of the distribution for this level is around 3,000 products per category as shown on figure 2.

Finally, at the Cat III level, the most populated categories are rich of more than 10,000 products each (Figure 2). The top 5 being POP ROCK MUSIC, PRINTER TONER, PRINTER CARTRIDGE, FRENCH LITTERATURE and OTHER BOOKS with nearly 70,000 items each. Most of the categories (nearly 2000 of them) count between 50 and 500 products.

Another way to look at the unbalancedness of the dataset is to consider the share of products with respect to the most populated categories. This is shown on figure 3 where the cumulative percentage of products is displayed as a function of the number of Cat III categories. The behavior is nearly exponential with 75 % of the products gathered in only 10 % of the categories. On the other end, the less populated 75 % of the categories account for only 10 % of the total number of products.

![figure_3]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/figure3.png)

## Duplicated images

The second aspect specific to our dataset might be the presence of duplicated images. Indeed, nothing prevents a reseller from using similar if not identical images to describe several of its products. Technical goods are a good example of products with distinct characteristics but identical appearance.

From an image classification point of view, the presence of duplicated images might be considered as a downside or an upside. It reduces the absolute size of the dataset but it may also help classifying a few products and making links between categories that contain identical images.

To trace back identical images, we use the [MD5 hash function](https://en.wikipedia.org/wiki/MD5) as defined. Images with the same 
hash key are labeled as identical. Although the MD5 hash function suffer from weaknesses that will prevent nearly identical images to be detected, it is efficient enough in our case where there is no will to hide duplicates by tricking the image.

![figure_4]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/figure4.png)

The distribution of the measured MD5 hash keys through the entire dataset is shown in Figure 4. Again, logarithmic scales have been used to account for the large range of values. Among the 12M images in total in the dataset, 6.85M images are uniquely defined and 75 % of the images appear at the most 10 times in the dataset. The image the most replicated appears 16,643 times!

## Winning the Cdiscount image classification challenge

Our image dataset was originally created for an image classification challenge that was held on the famous Kaggle platform between September and December 2017. The challenge involved more than 600 teams from all around the world and final results were quite impressive as the best solutions were able to correctly classify almost 80 % of the images of the test set. 

The evaluation metric was the accuracy of classification on a test set for which none of the categories was known. If you wishes to evaluate your categorizer on the test set, do not hesitate to contact the authors of this article. We will happily provide you with your test score.

![table_4]({{ site.baseurl }}/assets/images/DataScience/cdiscount_image_dataset/table4.png)

The name, final rank and score of the 3 winning teams is given in table 4. All 3 solutions are ensemble models that aggregate sub-models. They all rely on neural network architectures pre-trained on [_ImageNet_](http://www.image-net.org/) and they made a heavy use of GPUs to fine-tune those networks on our dataset. The neural network architectures that were used are listed below:
* ResNet
* InceptionResNetV2
* InceptionV3 
* ResNExt
* SE blocks 
* Dual Path Network

It is worth noting that none of the above mentioned techniques or architectures were described in the literature before 2016 for a challenge that was held in 2017! Also, all 3 solutions made use of the dropout technique to prevent overfitting and performed data augmentation via cropping, flipping and/or resizing operations.

At a more detailed level, the winning solution presents an interesting approach in which the trained neural networks are dedicated to products with a fix number of images. When more than one images are available, they are simply aggregated side by side in a larger image and fed into the dedicated model.

The 2nd solution took a similar approach for one of its sub-model by specializing neural networks for each number and rank of images. The competitor realized that both the number of images per product and the order of those images were not random and thus should be considered for classification.

Finally, a last worth mentioning originality was the use by the winning team of an OCR for products that were recognized as being books or CDs. This last trick probably made the small difference that made this solution the winning one!

Next, we hope to read from you. As already mentioned, we keep the test set labels cozy and warm for you so don't hesitate to contact us if you want to bench your classifier!
