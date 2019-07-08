---
layout: post
title:  "Link Prediction In Large-Scale Networks"
author: guillaume.lefloch
categories: [ en, data science ]
image: "assets/images/DataScience/link-prediction.jpeg"
mathjax: true
---

<p class="graf graf--h4" style="text-align: left;padding-left: 60px"><strong><em>A comparison of supervised and unsupervised approaches to infer missing links from an observed network </em></strong><em class="markup--em markup--p-em">by </em><a class="markup--anchor markup--p-anchor" href="https://www.linkedin.com/in/guillaume-le-floch-b1b632138/" target="_blank" rel="noopener"><em class="markup--em markup--p-em">Guillaume Le Floch</em></a><em class="markup--em markup--p-em"> (Data Scientist at </em><a class="markup--anchor markup--p-anchor" href="http://cdiscount.com" target="_blank" rel="nofollow noopener noopener noopener"><strong class="markup--strong markup--p-strong"><em class="markup--em markup--p-em">Cdiscount</em></strong></a><em class="markup--em markup--p-em">)</em></p>


<hr />

<h3 class="graf graf--h3">What is the point of predicting new links when you already have plenty of them ?</h3>
<p class="graf graf--p">If you have decided to read this article, you must either be very interested in Data Science or extremely bored right now. Whether this is the first or the second option, we are delighted to have you on board and wish that you will enjoy the ride through the link prediction problem with us.</p>
<p class="graf graf--p">On a more serious note, the goal of this paper is to find the best option to predict accurately future connections in a graph, which you can also call a network. Not a tiny, harmless network. No, we are talking about large-scale networks. The big and horrendous ones made of billion of nodes and edges which <strong class="markup--strong markup--p-strong">Facebook</strong>, <strong class="markup--strong markup--p-strong">Google </strong>(and <strong class="markup--strong markup--p-strong">Cdiscount</strong>) have had to deal with on a daily basis for the last few years.</p>

<blockquote class="graf graf--blockquote">What is the point of predicting new links when you already have plenty of them ?</blockquote>
<p class="graf graf--p">We have seen this question coming from a mile away, and we have got you covered, don’t worry. It is in the human nature (and even more in the Data Scientist one), to want more than what we already have. We don’t settle for the present, we want to know the future as well. Therefore, we need to find a way to perform predictions as accurate as possible.</p>


<p align="center"><img src="https://media.giphy.com/media/4cpqFamWB2dq0/giphy.gif"></p>
<p class="graf graf--p">Furthermore, a network is what we can call a dynamic structure as it evolves with time. For instance, social networks such as Facebook, Twitter, LinkedIn etc. change permanently as new connections appear while some others are removed from the graph.</p>
<p class="graf graf--p">For this particular example, one of the biggest challenges is to make accurate recommendations to the users. They may know somebody in real life, but aren’t connected with that person on their favourite social network. Thus, the target in this case would be to predict (and recommend) this association (link in the graph), in order to fix what can be seen as a mistake.</p>
<p class="graf graf--p">Link prediction can help rebuild the real life, but it could actually do more than just that. What we observe isn’t always ideal. An example would be terror attacks : given relationships between terrorists, you can build a network which represents who worked with who in the past. Link prediction can help predict future associations, allowing a government to monitor suspects and prevent them from committing a terror attack together. Biology is another area where link prediction can be a key asset, as human brains aren’t enough to predict all associations between molecules, having an artificial intelligence to do the job can be a massive boost.</p>
To put it in a nutshell, link prediction can be used for various purposes, in many different areas. In this article, we will focus mainly on the collaboration network case. We will work with the <a class="markup--anchor markup--p-anchor" href="https://snap.stanford.edu/data/com-DBLP.html" target="_blank" rel="noopener">DBLP dataset</a> (See [[1]](#ref1) for more details). This is a co-authorship network where two authors are connected if they publish at least one paper together, so we will try to predict relevant future collaborations here (we would like to avoid awkward situations).


<p align="center"><img src="https://media.giphy.com/media/26gJzrPTPiMNHrJLO/giphy.gif"></p>
<h3 class="graf graf--h3">The learning context: unsupervised vs. supervised</h3>
<p class="graf graf--p">In this section, we will discuss the possibilities at our disposal to perform predictions in a graph. As this is a special structure, we need to clarify a few points before getting started with prediction. Let’s start with a bit of theory and notations before practising.</p>

<h4 class="graf graf--h4">A little reminder of Graph Theory</h4>
<p class="graf graf--p">To ensure we are all speaking about the same things, let’s use the same vocabulary about graphs. And even if you already know this, a little reminder does no harm:</p>

<ul class="postList">
 	<li class="graf graf--li">From a mathematical point of view, a graph can be defined as $G = (V, E)$ with $V$ being the set of nodes and $E$ the set of edges.</li>
 	<li class="graf graf--li">A graph is undirected if the relationship goes both ways. Facebook is a good example of that : when someone is your friend, you automatically are his friend too. On the contrary, a graph is directed if the link goes from one node to another, but it isn’t reciprocal. Twitter illustrates this perfectly as you can follow somebody, but this individual doesn’t necessarily follow you in return.</li>
 	<li class="graf graf--li">We can define the graph’s adjacency matrix (of dimension $|V| × |V|$) as $A = [A_{ij}]$ with $(i,j) \in V$. For an undirected and unweighted graph :</li>
</ul>
<p style="text-align: center;">$$ A_{ij} = \begin{cases}1 &amp; \text{if}~i \leftrightarrow j \\0 &amp; otherwise\end{cases} $$</p>
<ul class="postList">
 	<li class="graf graf--li">A sequence is a succession of consecutive edges $\{i_1, i_2\}, \{i_2, i_3\}, …, \{i_{K-1}, i_K\}$.</li>
 	<li class="graf graf--li">A path between nodes $i$ and $j$ is a sequence of edges $\{i_1, i_2\}, \{i_2, i_3\}, …, \{i_{K-1}, i_K\}$ such as $i_1 = i$ and $i_K = j $ and each node in the sequence is distinct.</li>
 	<li class="graf graf--li">As we are going to heavily use the concept of <strong class="markup--strong markup--li-strong">neighborhood</strong>, let’s denote $\Gamma(u)$ the set of nodes which are directly linked with the node $u$ (they are its “neighbors”).</li>
 	<li>A distance between two nodes is given as the minimal number of edges to go from one node to another (shortest path).</li>
</ul>
&nbsp;
<p class="graf graf--p">The <a class="markup--anchor markup--p-anchor" href="https://snap.stanford.edu/data/com-DBLP.html" target="_blank" rel="noopener">DBLP dataset</a> which will be used for our experiments has the following properties:</p>

<ul class="postList">
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">317,080</strong> <strong class="markup--strong markup--li-strong">nodes </strong>(researchers).</li>
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">1,049,866</strong> <strong class="markup--strong markup--li-strong">edges </strong>(co-autorships between researchers).</li>
</ul>
<p class="graf graf--p">Yes, you are right. This is what we can call a large-scale network, and this is ideal in order to perform learning tasks, whether they are supervised or unsupervised. This will provide us with stability and confidence in the results we will get from the experiment.</p>
<p class="graf graf--p">Let’s now discover the learning process in the next part(s).</p>

<h4 class="graf graf--h4">The Creation of Training, Test and Validation Sets</h4>
<p class="graf graf--p">The part we are entering is a tricky one, so fasten your seat belt, we don’t want to lose you now. Splitting a dataset into training/test/validation sets isn’t a difficult concept to understand in normal circumstances. When it comes to graphs, it is a bit different. How can you split a graph to achieve a learning task ? First of all it is important to remember precisely our purpose : <strong class="markup--strong markup--p-strong">we want to predict links (edges) between nodes</strong>.</p>
<p class="graf graf--p">The first capital information is the following one : the predictive algorithm will take as input node pairs and evaluate whether the nodes present the properties to be linked in the future. In this paper, we will only look at nodes which are at distance 2 (e.g. nodes which don’t share a link but for which the shortest path to go from one to the other is made of 2 edges). What remains to be clarified now is the output : how can we create ground-truth labels from the graph ? The idea is to take a graph, hide some of its edges and monitor the results produced by the algorithm. For hidden links the label is 1, for non-existent links it is 0. Not clear enough yet ? No problem, let’s illustrate the concept with a minimal example :</p>
<p align="center"><img src="https://cdn-images-1.medium.com/max/800/1*uL5A7BU_oBJrNpFGIR0thg.png" /></p>
<p class="graf graf--p">From the left to the right we have :</p>

<ul class="postList">
 	<li class="graf graf--li">The “validation graph” which denote as $G_{valid} = (V, E_{valid})$ with : $V = \{A, B, C, D, E, F, G, H, I, J\}$ and $E_{valid} = \{(A,B); (A, D); (B, C); (B, D); (B, E); (C, D); (D, E); (D, F); (D, H); (D, G); (E, F); (E, I); (F, H); (F, I); (F, J); (I, J)\}$.</li>
 	<li class="graf graf--li">The “test graph” where we have hidden two edges : $G_{test} = (V, E_{test})$ with $E_{test} = E_{valid} \setminus \{(D, E); (D, H)\}$ thus $E_{test} \subset E_{valid}$.</li>
 	<li class="graf graf--li">The “training graph” where we have hidden four more edges : $G_{train} = (V, E_{train})$ with $E_{train} = E_{test} \setminus {(A, D); (C, D); (E, I); (F, J)}$ thus $E_{train} \subset E_{test}$.</li>
</ul>
<p class="graf graf--p">So, as you can see it is not that deep, it is just a matter of a graph which contains a subgraph which itself contains a subgraph…</p>
<p align="center"><img class="aligncenter" src="https://media.giphy.com/media/m7yzbDgdkWbmM/giphy.gif" width="234" height="234" /></p>
<p class="graf graf--p">If you are still firmly with us at this point, then you have guessed that our training set (with the corresponding labels) looks like the table below.</p>

<p align="center"><img src="https://cdn-images-1.medium.com/max/600/1*230lw-B4t405x6rFJk2FvQ.png" width="163" height="448" /></p>
<p class="graf graf--p">Make no mistake, the edge $(D, H)$ for example has the label $0$ here because it doesn’t exist in the Test Graph, even though it was originally present in the Validation Graph.</p>
<p class="graf graf--p">As we are evaluating all the 2-hop “missing link” node pairs we can see that the edges we have hidden have label of $1$ while the rest have a label of $0$. Let’s remember that this is just a minimal example, although we can already see several interesting facts :</p>

<ul class="postList">
 	<li class="graf graf--li">The number of node pairs to evaluate is fast-growing, we will let you imagine how it is like in a large-scale network (we will see it afterwards anyway).</li>
 	<li class="graf graf--li">The problem of <strong class="markup--strong markup--li-strong">class imbalance</strong> appears : there are far more $0$ labels, so we will have to deal with this problem later on..</li>
</ul>
&nbsp;
<p class="graf graf--p">Let’s now discover what are the unsupervised methods we can choose to perform link prediction in a graph, digging deepeer into the notions of <strong class="markup--strong markup--p-strong">neighborhood </strong>and <strong class="markup--strong markup--p-strong">local similarity</strong> in the process.</p>


<hr />

<h4 class="graf graf--h4">Unsupervised Learning : The Notion of Similarity Indices and Neighborhood</h4>
<p class="graf graf--p">If the nodes in the graph don’t possess properties, as is the case in our study, the only information available comes from the topological structure of the graph. By that, we mean the neighborhood of a node : how many neighbors has this node got ? How many neighbors these neighbors themselves have ? How are they organised ? As we are evaluating node pairs we can also look at how similar a node <em class="markup--em markup--p-em">u</em> can be to a node <em class="markup--em markup--p-em">v</em> by looking at their “distance” in the graph, the similarity of their local neighborhood.</p>
All of this has led to several local similarity indices such as Common Neighbors, Jaccard Similarity, Adamic-Adar Index, Resource Allocation, etc (more can be found in [[2]](#ref2) and [[3]](#ref3)). These indices will return a score $s \in \mathbb{R}$ which will be used to perform predictions. As it is explained in [[3]](#ref3), you will also need to set a threshold to define from which score you assign the label $1$. We sense that you may be asking which unsupervised method is the best to perform predictions. This is a tricky question as in some cases, one measure will outperform others, but in other cases it will be another one, etc.
<p class="graf graf--p">And what if we didn’t actually have to choose ? What if we let something else combine those local similarity indices to get a score in return ? You’ve got it right, we are heading straight to the Supervised Learning universe.</p>

<h4 class="graf graf--h4">Feature Engineering for Supervised Learning</h4>
We have already discussed how to obtain labels. Now we need features in order to perform Supervised Learning (Binary Classification). And yes, you guessed it, these features will come from the latest part we discussed. Based on <strong class="markup--strong markup--p-strong">Kolja Esders</strong>’s work in [[3]](#ref3), we will use unsupervised scores as features for our predictive model. We will also use the notion of <strong class="markup--strong markup--p-strong">Community</strong> (further details can be found in [[4]](#ref4)).
<p class="graf graf--p">The following features will be included in our learning/prediction task : <em class="markup--em markup--p-em">Common Neighbors (CN)</em>, <em class="markup--em markup--p-em">Jaccard Coefficient (JC)</em>, <em class="markup--em markup--p-em">Adamic-Adar index (AA)</em>, <em class="markup--em markup--p-em">Resource Allocation (RA)</em>, <em class="markup--em markup--p-em">Preferential Attachement (PA)</em>, <em class="markup--em markup--p-em">Adjusted-Rand</em> (AR) and <em class="markup--em markup--p-em">Neighborhood Distance</em> (ND) which are all local indices to which we will add the <em class="markup--em markup--p-em">Total Neighbors</em> (<em class="markup--em markup--p-em">TN</em>), <em class="markup--em markup--p-em">Node Degree</em> (<em class="markup--em markup--p-em">UD </em>et <em class="markup--em markup--p-em">VD</em>) and <em class="markup--em markup--p-em">Same Community</em> (<em class="markup--em markup--p-em">SC</em>) features.</p>
<p class="graf graf--p">They are defined as:</p>

<ul>
 	<li style="list-style-type: none">
<ul>
 	<li>$CN(u,v) = \left|\Gamma(u)~\cap~\Gamma(v)\right|$</li>
 	<li>$JC(u,v) = \frac{\left|\Gamma(u)~\cap~\Gamma(v)\right|}{\left|\Gamma(u)~\cup~\Gamma(v)\right|}$</li>
 	<li>$AA(u,v) = \sum_{w~\in~\Gamma(u)~\cap~\Gamma(v)} \frac{1}{log(\left| \Gamma(w)\right|)}$</li>
 	<li>$RA(u,v) = \sum_{w~\in~\Gamma(u)~\cap~\Gamma(v)} \frac{1}{\left| \Gamma(w)\right|}$</li>
 	<li>$PA(u,v) = \left| \Gamma(u) \right| \times \left| \Gamma(v) \right|$</li>
 	<li>$AR(u,v) = \frac{2(ad-bc)}{(a+b)(b+d)+(a+c)(c+d)}$</li>
 	<li>$ND(u,v) = \frac{\left| \Gamma(u)~\cap~\Gamma(v)\right|}{\sqrt{\left| \Gamma(u)~\times~\Gamma(v)\right|}}$</li>
 	<li>$TN(u,v) = \left| \Gamma(u)~\cup~\Gamma(v) \right|$</li>
 	<li>$UD = \left| \Gamma(u) \right|$</li>
 	<li>$VD = \left| \Gamma(v) \right|$</li>
 	<li>$SC(u,v) = \begin{cases} 1 &amp; \text{if}~u~\text{and}~v~\text{belong to the same community} \\ 0 &amp; \text{otherwise} \end{cases}$</li>
</ul>
</li>
</ul>
<p class="graf graf--p">As for <em class="markup--em markup--p-em">Adjusted-Rand</em> here is a table giving the meaning of $a$, $b$, $c$ and $d$ :</p>
<p align="center"><img class="aligncenter" src="https://cdn-images-1.medium.com/max/800/1*gag6JjfHYqtG42ymfDsM4w.png" width="472" height="124" /></p>
<p class="graf graf--p">Before going into predictions, we just need to discuss the evaluation metric which will help us determine whether Supervised Learning is better than the Unsupervised one (Spoiler alert : from Kolja Esders and our own experience in the past, it seems that it is the case) and it happens in the very next part.</p>

<h4 class="graf graf--h4">Evaluation metric</h4>
<p class="graf graf--p">The evaluation metric chosen in this study is a well-known one : the AUC. As it is a binary classification problem, it is ideal and will also allow us to plot the ROC curves of the method to illustrate the comparison between algorithm results. This will also free us from having to set a threshold for the unsupervised method.</p>
<p class="graf graf--p">Considering two independent and identically distributed observations $(X_1; Y_1)$ and $(X_2;Y_2)$, the AUC of a scoring method $S$ can be written in the following manner :</p>
<p style="text-align: center;">$$ AUC(S) = \mathbb{P}(S(X_1) \geq S(X_2)~|~(Y_1, Y_2) = (1,0))$$</p>
<p class="graf graf--p">In other words, a perfect algorithm (which would get an AUC of $1$) would give higher scores to every node pairs having a label of $1$ than node pairs having a label of $0$. This is just a matter of score order, whichever score is used.</p>
<p class="graf graf--p">In the next section we will put several algorithms face to face in the arena and compare their performances :</p>

<ul class="postList">
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">Resource Allocation</strong> (Unsupervised Method)</li>
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">Adamic-Adar</strong> (Unsupervised Method)</li>
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">Jaccard Coefficient </strong>(Unsupervised Method)</li>
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">Common Neighbors</strong> (Unsupervised Method)</li>
 	<li class="graf graf--li"><strong class="markup--strong markup--li-strong">Tree-based XGBoost</strong> (Supervised Method, combination of unsupervised scores with other features)</li>
</ul>
<p align="center"><img class="aligncenter" src="https://media.giphy.com/media/e37RbTLYjfc1q/giphy.gif" /></p>

&nbsp;
<h3 class="graf graf--h3">Experiments on the DBLP Dataset</h3>
<p class="graf graf--p">Before plotting the ROC curves and unleash the results, we will talk about data processing. As we pointed out previously, the class imbalance problem appears when dealing with huge networks. So after finding all the 2-hop missing links in our training and test graphs, we decided to randomly drop samples with labels zero in order to get a 50/50 balance for labels. This has led to these datasets :</p>

<ul class="postList">
 	<li class="graf graf--li">Train : 277,742 samples (node pairs)</li>
 	<li class="graf graf--li">Test : 150,348 samples (node pairs)</li>
</ul>
<p class="graf graf--p">These are huge datasets for both training and test which should help us avoid over-fitting. This will also give us confidence when it comes to the relevancy of the results.</p>
<p class="graf graf--p">Talking about them, you waited patiently for them, so here they are :</p>
<p align="center"><img class="aligncenter" src="https://cdn-images-1.medium.com/max/800/1*ZVex4KfhvCskk6toidjF0Q.png" /></p>
<p class="graf graf--p">He has just gone and done it again, hasn’t he ? The mighty Gradient Boosting algorithm has once again outperformed all his opponents. We will admit it wasn’t a completely fair contest though. This is what we can call an “easy” graph as we reach an AUC score of <strong class="markup--strong markup--p-strong">0.96 </strong>with <strong class="markup--strong markup--p-strong">XGBoost </strong>(which is very close to perfection), but methods such as <strong class="markup--strong markup--p-strong">Resource Allocation</strong> and the <strong class="markup--strong markup--p-strong">Adamic-Adar Index</strong> also performed very well with respective AUC scores of <strong class="markup--strong markup--p-strong">0.93</strong> and <strong class="markup--strong markup--p-strong">0.92</strong>. As we can see, <strong class="markup--strong markup--p-strong">Common Neighbors</strong> is a bit more limited in this case with an AUC of <strong class="markup--strong markup--p-strong">0.78</strong>, so only counting common friends may not be the best strategy if you want to have new friends it seems !</p>
<p class="graf graf--p">Tree-based boosting algorithms also provide “feature importance”, and an interesting fact here is that there seems to be a correlation between the feature importance of a similarity indice and its prediction quality :</p>
<p align="center"><img class="aligncenter" src="https://cdn-images-1.medium.com/max/800/1*S4zO6Xm5oJeFRKkMXc5OYQ.png" /></p>
<p class="graf graf--p">Resource Allocation was the “most important feature” according to this graph, and also as we saw previously, the best unsupervised method. It is quite similar to the Adamic-Adar index, with the only difference being the log at the denominator. In that regard, this may make <strong class="markup--strong markup--p-strong">RA </strong>more discriminating than <strong class="markup--strong markup--p-strong">AA </strong>as it penalises more the common neighbors which have many neighbors themselves.</p>

<h3 class="graf graf--h3">Discussion and Future Work</h3>
<p class="graf graf--p">From what we saw there, using a supervised method which combines unsupervised methods seems to be more efficient. This goes on to confirm Kolja Esders’s conclusions as well as our own past experience when working with networks.</p>
<p class="graf graf--p">This was an “easy” network as we got really high AUC scores, but depending on the complexity and noise in the graph you are working on, this can be more or less difficult to predict accurately future links. The gap between supervised and unsupervised scores can also widen with complex networks.</p>
<p class="graf graf--p">We decided to use the XGBoost algorithm but it is of course possible to use any other Machine Learning algorithm, so you can try to reproduce this experiment with your favourite binary classifier ! Data processing has been realised using the Networkit library, so you will need it (find more <a class="markup--anchor markup--p-anchor" href="https://networkit.iti.kit.edu/" target="_blank" rel="noopener">here</a>).</p>
<p class="graf graf--p">As we never settle for what we possess, the aim in the future would be to perform even better predictions. Building and adding new features to the model may help improve the performance as it would add information. Scaling data before feeding the model could also slightly improve the performance.</p>
<p class="graf graf--p">And this is how it ends ! We hope that you enjoyed this journey with us through the link prediction problem in a large-scale network. As the code and data are available in addition to this paper, feel free to reproduce this experience and even improve it if you can ! Thank you for your attention, it was a pleasure.</p>

<h3 class="graf graf--h3">Further readings</h3>
* <a name="ref1"></a>[1] J. Yang and J. Leskovec, (2012). _Defining and Evaluating Network Communities based on Ground-truth_ (ICDM [http://snap.stanford.edu/data/com-DBLP.html](http ://snap.stanford.edu/data/com-DBLP.html)).
* <a name="ref2"></a>[2] David Liben-Nowell and Jon Kleinberg, (2007). _The Link-Prediction Problem for Social Networks._
* <a name="ref3"></a>[3] Kolja Esders, (2015). _Link Prediction in Large-scale Complex Networks_. Bachelor’s Thesis at the Karlsruhe Institute of Technology.
* <a name="ref4"></a>[4] Vincent D. Blondel, Jean-Loup Guillaume, Renaud Lambiotte and Etienne Lefebvre (2008). _Fast unfolding of communities in large networks_