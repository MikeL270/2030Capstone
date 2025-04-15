<script setup lang="ts">
import Header from './components/Header.vue'
import Footer from './components/Footer.vue'

</script>

<template>
  <header>

    <div class="wrapper">
    <Header />
    </div>
  </header>

  <main>
   
  </main>
  <footer>
    <Footer />
  </footer>
</template>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    flex-direction: column;
    position: absolute;
    width: 100%;
    height: 10vh;
    top: 0;
    left: 0;
    padding-right: calc(var(--section-gap) / 2);
    color: rgb(255, 255, 255);
    background-color: rgb(51, 51, 51);
    border-bottom: 1px solid rgba(255, 255, 255, 0.788);
    padding: 1%;
  }

  footer {
    display: flex;
    flex-direction: column;
    place-items: center;
    align-items: center;
    justify-content: center;
    position: absolute;
    bottom: 0;
    left: 0;
    background-color: rgb(51, 51, 51);
    width: 100%;
    height: 15vh;
    padding: 1%;
    color: white;
    border-top: 1px solid rgba(255, 255, 255, 0.788);;

  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
