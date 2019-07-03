This article describes our Kubernetes Setup on Azure with multi-GPU agents for running tensorflow / tensorflow-serving deep learning containers.

ACS Engine
----------

ACS Engine allows you to quickly set up a kubernetes cluster on azure.

ACS Engine essentially a tool generating parametrized Azure RM
deployments.

Prequisites : Go and Git.

Follow the [Installation guide on github.](https://github.com/Azure/acs-engine/blob/master/docs/acsengine.md)

### Cluster definition

Start with given examples to obtain this *kubernetes.json* :

`{`\
` "apiVersion": "vlabs",`\
` "properties": {`\
`   "orchestratorProfile": {`\
`     "orchestratorType": "Kubernetes",`\
`     "orchestratorVersion": "1.6.2"`\
`   },`\
`   "masterProfile": {`\
`     "count": 3,`\
`     "dnsPrefix": "rd-kub-gpu",`\
`     "vmSize": "Standard_D2_v2",`\
`     "OSDiskSizeGB": 100`\
`   },`\
`   "agentPoolProfiles": [`\
`     {`\
`       "name": "agentpoolc",`\
`       "count": 3,`\
`       "vmSize": "Standard_D14_v2_Promo",`\
`       "OSDiskSizeGB": 100,`\
`       "availabilityProfile": "AvailabilitySet"`\
`     },`\
`     {`\
`       "name": "agentpoolg",`\
`       "count": 3,`\
`       "vmSize": "Standard_NC6",`\
`       "OSDiskSizeGB": 100,`\
`       "availabilityProfile": "AvailabilitySet"`\
`     }`\
`   ],`\
`   "linuxProfile": {`\
`     "adminUsername": "XXXXXXXX",`\
`     "ssh": {`\
`       "publicKeys": [`\
`         {`\
`           "keyData": "ssh-rsa XXXXXXXX[...]XXXXXX"`\
`         }`\
`       ]`\
`     }`\
`   },`\
`   "servicePrincipalProfile": {`\
`     "servicePrincipalClientID": "XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX",`\
`     "servicePrincipalClientSecret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"`\
`   }`\
` }`

Here we basically have 3 VM pools : one of 3 little master nodes,
another of 3 CPU oriented, and a last one GPU oriented.

**Warning** : The kind of VM you want for this kind of machine learning
project (and supported under linux) are in the **NC\_** range with
nvidia K80 GPU.

More info on N-series features and availabilty on Azure Blog : <https://azure.microsoft.com/en-us/blog/azure-n-series-general-availability-on-december-1/>

More info about the cluster definition using ACS engine :
<https://github.com/Azure/acs-engine/blob/master/docs/clusterdefinition.md>

### Deployment files generation

As simple as :

`./acs-engine generate kubernetes.json`

ACS engine will render ready to use Azure RM deployments under
subdirectory *\_output/Kubernetes-<clusterid>/\**

Specifically we will be interested in these 2 files : *azuredeploy.json*
and *azuredeploy.parameters.json*.

### Deploy

We will now be able to deploy our cluster using our usual ansible
playbooks or like this, using Azure CLI :

`az group deployment create \    --name "`<DEPLOYMENT NAME>`" \    --resource-group "`<resource_group>`" \    --template-file "./_output/`<INSTANCE>`/azuredeploy.json" \    --parameters "./_output/`<INSTANCE>`/azuredeploy.parameters.json"`

**Warning** : NC\_ range VMs are not available in every Azure region.
Here we had to subscribe a resource group in northeurope.

Here is an interesting tool microsoft provides to explore availability
by VM type and region :
<https://azure.microsoft.com/en-us/regions/services/>

Nvidia GPUs & multi gpu
-----------------------

We began with provisionning classical GPU VMs aside our k8s cluster to
start our developments. Then in a second time we activated the GPUs
hosts on our k8s cluster.

*Note* : Newer versions of ACS engine deploy kubernetes out-of-the-box "GPUs-enabled" ( [see the merged pull request](https://github.com/Azure/acs-engine/pull/385>)).

### GPU-enabled machine


#### CUDA

CUDA allows to use the GPUs for running generalistic computing in
parallel.

Install CUDA from the Nvidia repositories:

Using Apt, add the repo
http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86\_64
/ to your sources.list.d entries

and their gpg key : developer.download.nvidia.com/compute/cuda/repos/GPGKEY

We are now using v8.0.61-1.

<https://medium.com/@gooshan/for-those-who-had-trouble-in-past-months-of-getting-google-s-tensorflow-to-work-inside-a-docker-9ec7a4df945b>

<https://developer.nvidia.com/compute/cuda/8.0/Prod2/docs/sidebar/CUDA_Installation_Guide_Linux-pdf>

#### cuDNN

cuDNN is a library implementing neural networks primitives and deep
learning over Nvidia GPUs.

You have to sign in the nvidia developer program :
<https://developer.nvidia.com/cudnn>

then [download the linux runtime
(.deb)](https://developer.nvidia.com/rdp/cudnn-download) and install it : 
`dpkg -i libcudnn6\_6.0.21-1+cuda8.0\_amd64.deb`

We are now using cudnn v6.0.21-1.


#### Check

We can then check our installation :

*nvidia-smi* will list the GPUs if they are enabled.

`lsmod | grep -i nvidia && ls -alh /dev | grep -i nvidi`

### Nvidia-docker

To enable our containers to use the GPUs, we need the *nvidia-docker*
tools.

The package is composed of 2 tools :

nvidia-docker-plugin : docker discovery plugin on the host : modules and
libs are listed. works as a cli and a REST API is also presented.

nvidia-docker : a cli wrapping around the docker CLI and setting paths
to modules and libraries provided by nvidia-docker-plugin API.

`wget
https://github.com/NVIDIA/nvidia-docker/releases/download/v1.0.1/nvidia-docker_1.0.1-1_amd64.deb`

`dpkg -i nvidia-docker\_1.0.1-1\_amd64.deb`

Once the install is OK, running the following :

`nvidia-docker run --rm nvidia/cuda nvidia-smi`

Should validate a container has access to the host's GPU.

### Kubernetes

Now that we have each host correctly configured, it is time to set up
our k8s nodes to handle GPU access for their containers.

#### Kubelet configuration

As the time of the writing, using k8s v&gt;1.6, the kubelet option to
enable GPU support is *feature-gates=Accelerators=true.*

Previously the equivalent option was the flag :
--experimental-nvidia-gpus.

So add this option to the kubelet statup args. Edit
*/etc/systemd/system/kubelet.service* like this for instance :

`${KUBELET_IMAGE} \`\
`        /hyperkube kubelet \`\
`        --feature-gates=Accelerators=true \`\
`        --kubeconfig=/var/lib/kubelet/kubeconfig \`

Then restart the kubelet service and you are done.

### GPU known Problems

Sometimes, the GPU-enabled containers silently stop working.

The only way to resolve this seems to send a node restart via azure cli
or azure portal.

The kernel shows some errors

\
`# dmesg `\
`[...]`\
`[Thu Jun 29 11:32:39 2017] INFO: task kworker/2:3:1275 blocked for more than 120 seconds.`\
`[Thu Jun 29 11:32:39 2017]       Tainted: P           OE   4.4.0-81-generic #104-Ubuntu`\
`[Thu Jun 29 11:32:39 2017] "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.`\
`[Thu Jun 29 11:32:39 2017] kworker/2:3     D ffff883c5bed3b58     0  1275      2 0x00000000`\
`[Thu Jun 29 11:32:39 2017] Workqueue: events os_execute_work_item [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  ffff883c5bed3b58 ffffffff810b2c1c ffff883c5fe22a00 ffff883c6102c600`\
`[Thu Jun 29 11:32:39 2017]  ffff883c5bed4000 ffff883c5d4a6b08 ffff883c6102c600 ffff883c5bed3e10`\
`[Thu Jun 29 11:32:39 2017]  ffff883c60a72bc8 ffff883c5bed3b70 ffffffff8183c955 7fffffffffffffff`\
`[Thu Jun 29 11:32:39 2017] Call Trace:`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810b2c1c>`] ? __enqueue_entity+0x6c/0x70`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8183c955>`] schedule+0x35/0x80`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8183faa5>`] schedule_timeout+0x1b5/0x270`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810b57ca>`] ? check_preempt_wakeup+0xfa/0x220`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8183ea0f>`] __down+0x7f/0xd0`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810ca6a1>`] down+0x41/0x50`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc10a7a37>`] os_acquire_semaphore+0x37/0x40 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc10a7a4e>`] os_acquire_mutex+0xe/0x10 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc164ba48>`] _nv017509rm+0x18/0x30 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc15e467d>`] ? _nv019728rm+0x3d/0x120 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc14568e8>`] ? _nv018215rm+0x118/0x200 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc164fbc5>`] ? _nv000785rm+0x225/0xcd0 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc16538e9>`] ? rm_execute_work_item+0x49/0xc0 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff811ed901>`] ? kmem_cache_alloc+0xe1/0x1f0`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc10a7d01>`] ? os_alloc_mem+0x71/0xf0 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffffc10a7e16>`] ? os_execute_work_item+0x46/0x70 [nvidia]`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8109a585>`] ? process_one_work+0x165/0x480`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8109a8eb>`] ? worker_thread+0x4b/0x4c0`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff8109a8a0>`] ? process_one_work+0x480/0x480`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810a0c25>`] ? kthread+0xe5/0x100`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810a0b40>`] ? kthread_create_on_node+0x1e0/0x1e0`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff81840e0f>`] ? ret_from_fork+0x3f/0x70`\
`[Thu Jun 29 11:32:39 2017]  [`<ffffffff810a0b40>`] ? kthread_create_on_node+0x1e0/0x1e0`

links :
<https://devtalk.nvidia.com/default/topic/876218/upgrading-from-346-47-to-352-41-on-aws-causes-kworkers-to-lockup-on-boot-module-load-and-prevents-u/>

Tensorflow : To Be Continued
----------------------------
