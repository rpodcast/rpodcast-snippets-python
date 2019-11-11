Notes on getting the lambda layer with feedgen working
* Create a cloud9 instance on AWS and load the lambda function
* Follow [this guide](https://aws.amazon.com/premiumsupport/knowledge-center/cloud9-deploy-lambda-external-libraries/) on the AWS docs to install `lxml` first, then install the remaining modules like `feedgen` and `pcloud`.
* Upload the new version of the lambda function by clicking the upload button 
* In the lambda config page on AWS, make sure that the python 3.6 runtime is selected!

Old notes (possibly delete)
* Create new EC2 image based on amazon linux 2 distribution. Create a new keypair and save the `pem` file to the local machine.  Use [these instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html) to connect via SSH
* Install python3, pip, and virtual environments as detailed [here](https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-python3-boto3/)
* Launch virtual environment per above link. Install `lxml`, `feedgen`, and `pcloud` python modules via `pip`.
* Adapt solution from [this SO post](https://stackoverflow.com/questions/36397171/aws-lambda-not-importing-lxml/37450406#37450406) to create zip file.  Should look something like this:

```
for dir in lib64/python3.7/site-packages \
    lib/python3.7/site-packages
do
    if [ -d $dir ] ; then
        pushd $dir; zip -r ~/deps.zip .; popd
    fi
done 
```

* Exit session and download zip file to local machine via `scp`
* Upload zip file as new layer in lambda layer management interface