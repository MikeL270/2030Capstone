<template>
 <div class="Page-Content">
    <h1> Welcome to the Pronghorn Cropper! </h1>
    <br>
    <h2> Introduction </h2>
    <p> This webapp is a work in progress. The goal is to produce a large amount of training data 
        for a computer vision wildlife census project. Most features are missing as this project is 
        in a very early stage of development. Since there is currently only one developer for the 
        webapp, API, and database a minimum skeleton of the project has been laid out with plans to 
        revisit components as time allows. </p>

    <br>
    <h2> Instruction to annotators</h2>
    <p> Chances are if you're reading this you have been hired as an annotator. Refer to the navigation
        menu to the left and take some time familiarizing yourself with it. Note You will only really ever need
        to interact with the annotation component of this app, it is denoted by the square with points
        at each corner under the 'home' button. Notice that the 'Hamburger Menu' at the top of the navigation
        toggles a labeled view of the menu, this can be used to identify which component you need.</p>
    <br>
    <h2> Details </h2>
    <p> This webapp is a S.P.A. (Single Plage Application) Built with Typescript on Vue.js. It is 
        designed to be an easy to use tool for computer vision based wildlife census projects to create
        training data and eventually perform the census itself. The project is built on top of a python 
        based Restful API and Postgres database. This webapp makes use of a 'router,' a special Vue 
        module that enables navigation of the app without making requests back to the server, resulting in 
        a very smoothe experience. We do make use of lazy loading for our modules to reduce the upfront load 
        times, this means that each component is only loaded (and then cached) from the server when selected.
        This can lead to a slight wait when first loading large components. This trade-off was made to reduce 
        overall load times and memory usage of the webapp on average. 
    </p>
 </div>
</template>

