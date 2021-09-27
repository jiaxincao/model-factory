This doc explains how you should you model factory to develop and execute your model building pipeline. In this example, let's develop a model factory pipeline to do a [digit classification task](https://scikit-learn.org/stable/auto_examples/classification/plot_digits_classification.html#sphx-glr-auto-examples-classification-plot-digits-classification-py).

This doc is divided into two sections. The first section talks about how you should develop a model building pipeline. The second one talks about how to set up continuous model buliding runs with model factory triggers.


# Develop Your Pipeline

## Step 1: Create Your Pipeline

The first step of your model building pipeline development is to create your pipeline boilerplate code. In order to do so, run the following command

```
mf pipeline create digit_classification_model_pipeline
```

## Step 2: Define Your Dockerfile
Next, let's define your dockerfile, which is docker/digit_classification_model_pipeline_base_image.dockerfile. The file consists of three sections. Please add any needed packages in section 2. In our case, the file looks like this.

```
################################################################################
# Section 1: Parent Image
################################################################################
ARG DOCKER_REGISTRY
FROM 172.31.27.140:5000/model_factory_base_image


################################################################################
# Section 2: Pipeline Custom Package Installation
################################################################################

# If you need any packages or special setup for your pipeline, please put them in section 2.


################################################################################
# Section 3: Set up environment variables
################################################################################
RUN echo "export PYTHONPATH='/model-factory/src'" >> /root/.bashrc
ENV PYTHONPATH='/model-factory/src'
```

## Step 3: Develop Your Code
To implement the model building pipeline code in pipelines/digit_classification_model_pipeline/main.py, we basically assembly the code in [scikit-learn's official website](https://scikit-learn.org/stable/auto_examples/classification/plot_digits_classification.html#sphx-glr-auto-examples-classification-plot-digits-classification-py). We also added our own part to save to model to our model registry. Here's the final code:

```
################################################################################
# Pipeline imports and global initializations.
################################################################################
import logging
import pickle

from core.model_registry import ModelRegistry
from core.execution_context import ExecutionContext

# Standard scientific Python imports
import matplotlib.pyplot as plt

# Import datasets, classifiers and performance metrics
from sklearn import datasets, svm, metrics
from sklearn.model_selection import train_test_split


################################################################################
# Pipeline code.
################################################################################
def main(params):
    logging.info("Start executing pipeline digit_classification_model_pipeline")

    # Please start implementing your pipeline logics from here.

    digits = datasets.load_digits()

    _, axes = plt.subplots(nrows=1, ncols=4, figsize=(10, 3))
    for ax, image, label in zip(axes, digits.images, digits.target):
        ax.set_axis_off()
        ax.set_title('Training: %i' % label)

    # flatten the images
    n_samples = len(digits.images)
    data = digits.images.reshape((n_samples, -1))

    # Create a classifier: a support vector classifier
    clf = svm.SVC(gamma=0.001)

    # Split data into 50% train and 50% test subsets
    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, test_size=0.5, shuffle=False)

    # Learn the digits on the train subset
    clf.fit(X_train, y_train)

    # Predict the value of the digit on the test subset
    predicted = clf.predict(X_test)

    print(
        f"Classification report for classifier {clf}:\n"
        f"{metrics.classification_report(y_test, predicted)}\n"
    )

    # Save the model to file
    pickle.dump(clf, open("model.dat", "wb"))

    # Upload the model to model registry.
    model_id = ModelRegistry.register("digit_classification_model", ExecutionContext.job_id)
    ModelRegistry.push(model_id, "./model.dat")
```


## Step 4: Debug Your Code
There is a good chance that you need to debug your code before make it run from start to finish. In order to debug your code, create a dev container first with
```
mf dev container digit_classification_model_pipeline
```

and then use the following command to run your pipeline inside of the container.
```
mf job create digit_classification_model_pipeline --mode inplace
```

You can modify your code anytime, and then run the job again without the need of restarting the dev container, because your pipeline code is mapped into the container. You can also use tools to debug your code, e.g., pdb or pudb.


## Step 5: Submit Your Job
Once your are done with debugging, quit the container, and run

```
mf job create digit_classification_model_pipeline
```

To check your job status, use
```
mf job list
```

To check your model generated by the job, use
```
mf model list
```

Now, your model is uploaded to s3 (or MinIO) and it is ready to be consumed by any service.


# Set Up Continuous Model Buliding Runs
Model factory trigger is a mechanism for you to do rule based actions. A trigger is checked every one minute, if the rule is met, the action is triggered. One of the most important trigger is CronTrigger. Next, we are going to create a trigger to schedule your pipeline at 11:00 every day (UTC time).

The first step is to build a pipeline image for the trigger to use

```
mf pipeline build-image digit_classification_model_pipeline --image-tag online
```

then, create the trigger to run the job at the scheduled time
```
mf trigger create digit_classification_model_pipeline CronTrigger -i '{
    "schedule": "0 11 * * *",
    "operator_id": "pipelines.digit_classification_model_pipeline.main.main",
    "pipeline_name": "demo_pipeline",
    "docker_image_repo": "172.31.27.140:5000/digit_classification_model_pipeline",
    "docker_image_tag": "digit_classification_model_pipeline",
    "storage_request": "1G"
}'
```

once the trigger is created, you can use the following command to check the jobs scheduled by the trigger

```
mf trigger list-jobs digit_classification_model_pipeline
```
