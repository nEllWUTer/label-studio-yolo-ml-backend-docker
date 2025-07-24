# Label studio with yolo ML backend

## [Label-studio](https://github.com/HumanSignal/label-studio)

### Create docker network

```cmd
docker network create label-studio-network
```

### Build label-studio service

```cmd
mkdir mydata
docker compose up
```

### API Tokens settings

Now, you need change *API Tokens settings*  
Left side burger menu => Organization => API Tokens settings

1. disable *Personal Access Tokens*
2. enable *Legacy Tokens*

## [Label-studio-ml-backend-yolo](https://github.com/HumanSignal/label-studio-ml-backend/tree/master/label_studio_ml/examples/yolo)

To start using the models, use **docker-compose.ml-yolo-backend.yml** to run the ML backend server.

You will need to set ***LABEL_STUDIO_URL*** and ***LABEL_STUDIO_API_KEY*** environment variables to allow the ML backend access to the media data in Label Studio.  
To get the Label Studio API key:

1. Login into Label Studio
2. Сlick the user settings in the right-hand corner of the application
3. Select Accounts & Settings from the dropdown menu and note the Access Token.  

To solve the **localhost issue** you will need to add **extra_hosts** in **docker-compose.yml**

```yml
    extra_hosts:
      - "localhost:172.**.0.1"
```

### Custom YOLO model

1. Mount your model as `/app/models/<your-model>.pt` inside of your Docker.  
2. Add `model_path="<your-model>.pt"` to the control tag in the labeling configuration, e.g.:

```xml
  <RectangleLabels model_path="my_model.pt">
```

### Build the ML backend

Before build you need to set **ENVIRONMENT**

```cmd
export TEST_ENV=true (Linux)
set TEST_ENV=true (Windows)
```

Build ML backend

```cmd
docker compose -f docker-compose.ml-yolo-backend.yml up --build
```

## Connect label-studio service with ml-backend

### 1 Create project

Open [label-studio](http://localhost:8080) **=> Create**

### 2 Set custom template for labeling interface

You need paste xml config to **Labeling setup > Custom template**, during project creation.

``` xml
<View>
  <Image name="image" value="$image"/>
  <RectangleLabels name="label" toName="image" model_path="pigs_v10.pt" model_score_threshold="0.25">
    <Label value="pig" category="0" background="blue" predicted_values="pig"/>
    <Label value="human" category="1" background="red" predicted_values="human"/>
  </RectangleLabels>
</View>
```

`model_path="pigs_v10.pt"` - custom yolo model

### 3 Connect with ml-backend

#### - Go to **Project settings => Model => Connect Model**  

    Enter a **Name** of model and **Backend URL**  
    *Default ML-Backend URL - http://<Backend-IP>:9090/*  
    Enable **Interactive preannotations**!  
    Now you can check connection with ml-backend by sending a **Test Request** (Choose it in *** - burger menu)  
    ***200 - Connection is OK***

#### - Add images to Label Studio  

There are several ways to add images to the label studio

1. Import files directly
2. Dataset URL
3. Cloud storage(Local storage)  
  Project settings => Cloud Storage => Add source storage => Choose Storage type => Local files  
  Now you need enter a **Absolute local path to images**  

    - Local path inside docker container - /label-studio/data/%%  
    - Copy your images to label-studio/mydata project folder  
  
    Enable **Treat every bucket object as a source file**  
    **Check connection => Add storage => Sync now**  

#### Open any task in the Data Manager and see the predictions from the YOLO model  
