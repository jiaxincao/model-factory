<template>
<b-navbar class="header-bar" type="dark" variant="dark">
  <b-navbar-brand class="brand" href="/jobs">Model Factory Dashboard</b-navbar-brand>

  <b-navbar-nav class="navbar">
    <div class="main-bar">
      <b-nav-item class="nav-bar-item" :active="path_name=='/jobs'" href="/jobs">Jobs</b-nav-item>
      <b-nav-item class="nav-bar-item" :active="path_name=='/triggers'" href="/triggers">Triggers</b-nav-item>
      <b-nav-item class="nav-bar-item" :active="path_name=='/models'" href="/models">Models</b-nav-item>
    </div>
  </b-navbar-nav>
</b-navbar>
</template>

<script>
export default {
  name: 'Header',
  data() {
    return {
      "path_name": window.location.pathname.toLowerCase(),
      "region": this.$cookies.get("region") || "us-west",
    }
  },
}
</script>

<style scoped>
.header-bar {
    height: 60px;
    width: 100%;
    min-height: 60px;
    min-width: 1000px;
    background-color: #404040;
}

.navbar {
    width: 100%;
}

.main-bar {
    display: flex;
}

.brand {
    width: 300px;
    height: 100%;
}

.nav-bar-item {
    margin-left: 5px;
    margin-right: 5px;
}
</style>
