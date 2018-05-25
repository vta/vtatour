# VTA Tour #

## What is this repository for? ##

* Repository for **VTA Tour** website. 
* Version: 1.0

## How do I get set up? ##

### Requirements ###
* NodeJS
* NPM
* Bower
* Gulp

### Set up your dev environment ###
1. Clone the repository
2. Go to the "web" folder
3. Run "npm install && bower install" to install the *node_modules* and *bower* dependencies
4. Run "gulp serve" to run the application


### Deploy to firebase ###
1. Go to vta project main folder
2. Update the file .firebaserc with your project id
3. run the build script: "./build"
4. Run the command: "firebase deploy"


## Important topics ##

### Base Technology Stack ###
* Firebase (Backend)
* Polymer (Frontend)

### Git branch model ###
The Git branch model that will be followed is the one proposed by GitFlow and documented [here](http://nvie.com/posts/a-successful-git-branching-model/).
