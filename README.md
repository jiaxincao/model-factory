# Model Factory

Machine learning today is powering many businesses today, e.g., search engine, e-commerce, news or feed recommendation. Training high quality ML models is critical to all of these systems.

However, training a model is not trivial. Traditionally, engineers use single devvm to train models. It might be doable if you were only to build a few models. If you are interested in exploring hundreds or even thousands of ideas, repeating the workflow manually will be a painful process.

There are many issues with the above workflow:
* **Hard to scale**
* **No tracking**
* **No monitor**
* **No end-to-end automation**
* **Not easy to share with others**
* **No centralized model management**

The above pain points really slows engineers down when they are developing their ML models. Model factory is a project that targets at addressing the above issues.

# Background
There are existing work in the industry which tries to address the above issues as well, e.g., Facebook fblearner, Google Kubeflow.

The key difference bewteen model factory and other projects is that model factory promotes a **pure python based authoring experience**, while most others uses DAG (Directed Acyclic Graph). The phylosophy gives model factory the following advantages:
* **Easy to learn**: there is almost no learning curve. As long as you know how to write python, you know how to use model factory.
* **More flexible**: control flow logics can be easily implemented on it.
* **Allow communication between nodes**: free form communication can be done between operators, which opens up the possibility of building distributed training on top of model factory.


# Installation
Please follow the [Installation](docs/installation.md) page to deploy model factory in your production or testing environment.


# Development Guide
Please follow the [Development Guide](docs/development_guide.md) page to try out your first model factory pipeline.
