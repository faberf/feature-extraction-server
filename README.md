# Feature Extraction Server

This server accepts both images and text as input and performs various AI tasks, such as image image_captioning. It uses a modular design that allows new tasks and models to be easily added. The purpose of this server is to maintain a uniform input / output specification for each AI task, regardless of the specifics of the model used. This allows models to be swapped more easily.


## Server Side

In order to perform image_captioning or other tasks, the server must first be started. As a prerequisite, install the required packages:
```bash
pip install -r environment.txt
```

To run the server, simply run app.py:

```bash
python app.py
```

The server will start running on localhost on port 5000.


## Client Side

To perform an AI Task, send a POST request to the `/extract` endpoint with a JSON body. The JSON should have the key 'task' set to the intended task and any additional data required to execute the task. It can optionally contain 'model' to specify the model, and 'config' to specify any additional arguments. 

Here is an example of how to caption an image using a curl command:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"image": "<base64-encoded-image>", "task": "caption", "model": "blip", "config": {"top_k":50}}' http://localhost:5000/extract
```

this returns 

```json
["a black and white photo of a house"]
```

### Image Captioning

This service allows you to generate a text caption that describes the visual content of an image. The API requires a JSON body with specific keys:

| Key | Required | Description |
| --- | --- | --- |
| `task` | Yes | This should be set to `image_captioning` |
| `image` | Yes | A base64 encoded image string. Optionally, the encoded string can have a data URL prefix (e.g., `data:image/png;base64,iVBORw0KGgoA...`) |
| `model` | No | The model which should execute the captioning |
| `config` | No | Any additional arguments (depending on the model) |

The API responds with a list of strings that caption the image. Typically, this list will contain one item, but depending on the model and configuration used, it may contain multiple items. In **Batch Mode**, if the 'image' key is set to a list of strings, the server will return a list of lists (one list for each image in the input).




### Conditional Image Captioning

This service allows you to use a text prompt to condition an image captioning task. The API requires a JSON body with specific keys:

| Key | Required | Description |
| --- | --- | --- |
| `task` | Yes | This should be set to `conditional_image_captioning` |
| `image` | Yes | A base64 encoded image string. Optionally, the encoded string can have a data URL prefix (e.g., `data:image/png;base64,iVBORw0KGgoA...`) |
|`text` | Yes | A specified prefix for the caption that should be generated. For example `Question: What is depicted in this photograph? Answer:` |
| `model` | No | The model which should execute the captioning |
| `config` | No | Any additional arguments (depending on the model) |

The API responds with a list of strings that caption the image. These strings do not include the specified prefix. In **Batch Mode**, if the 'image' or 'text' key is set to a list of strings, the server will return a list of lists (one list for each image in the input).


### Automated Speech Recognition

This service allows you to generate text from speech. The API requires a JSON body with specific keys:

| Key | Required | Description |
| --- | --- | --- |
| `task` | Yes | This should be set to `automated_speech_recognition` |
| `audio` | Yes | A base64 encoded audio. Optionally, the encoded string can have a data URL prefix (e.g., `data:audio/wav;base64,iVBORw0KGgoA...`) |
| `model` | No | The model which should execute the speech recognition |
| `config` | No | Any additional arguments (depending on the model) |

The API responds with a string of recognized audio. In  **Batch Mode**, if the 'audio' key is set to a list of strings, the server will return a list of strings.

### Zero Shot Image Classification

This service allows you to to match an image to a class from a catalogue of classes. The API requires a JSON body with specific keys:

| Key | Required | Description |
| --- | --- | --- |
| `task` | Yes | This should be set to `zero_shot_image_classification` |
| `image` | Yes | A base64 encoded image string. Optionally, the encoded string can have a data URL prefix (e.g., `data:image/png;base64,iVBORw0KGgoA...`) |
|`classes` | Yes | A list of strings that represents the catalogue of classes |
| `model` | No | The model which should execute the classification |
| `config` | No | Any additional arguments (depending on the model) |

The API responds with a list of floating point numbers between 0 and 1 that represent the probability that the image belongs to a class. In **Batch Mode**, if the 'image' key is set to a list of strings, the server will return a list of lists (one list for each image in the input).

### Object Detection

This service allows you to identify regions of an image that contain objects. The API requires a JSON body with specific keys:

| Key | Required | Description |
| --- | --- | --- |
| `task` | Yes | This should be set to `object_detection` |
| `image` | Yes | A base64 encoded image string. Optionally, the encoded string can have a data URL prefix (e.g., `data:image/png;base64,iVBORw0KGgoA...`) |
| `model` | No | The model which should execute the object detection |
| `config` | No | Any additional arguments (depending on the model) |

The API response with a dictionary that includes the keys `boxes`, `labels`, `scores`. Each key is maps to a list of the same length, the number of detected objects. An item in the `boxes` list is a list with four values (xmin, ymin, xmax, ymax), an item in the `labels` list is the name of the object as a string, an item in the `scores` is a floating point number between 0 and 1 which represents the confidence that the object was detected correctly.

## Extending the Server

The server is designed to be easily extensible with new tasks and models. To add a new task or model, follow these steps:

1. **Add a new task**: To add a new task, edit the tasks module so that it implements a wrapper function. Make sure you also update the `tasks` dictionary and the `default_models` dictionary (also in the tasks module).

2. **Add a new model**: To add a new model, simply add a new Python file in the models directory. For each task that this model is able to do you can implement a function that is named after the task.

For example, if you want to add a new audio classification model, you might create a new file called 'cool_model.py'. In 'cool_model.py', you would define your classification function like this:

```python
def audio_classification(image, other_arg, more_args):
    # Your model's image classification code here
    pass
```
Of course, make sure to edit the tasks module if the task 'audio_classification' does not exist yet. 
After these steps, you can specify 'audio_classification' as the task and 'cool_model' as the model in your POST request to the /extract endpoint.

## API Endpoints

- **POST /extract**: Perform extraction with the specified task (or default task) and model (or default model). All other arguments will be passed to the task wrapper which wraps the models functions.

- **GET /tasks**: Get a list of all available tasks.
<!-- 
- **GET /models/\<task>**: Get a list of all models available for the specified task. -->