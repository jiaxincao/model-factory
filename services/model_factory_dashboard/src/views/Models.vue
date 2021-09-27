<template>
<div>
  <div class="filter_card">
    <div class="filter_title">
      Model Filters:
    </div>
    <div class="filter_group">
      <div class="filter_key" >Model ID: </div>
      <b-form-input v-model="model_id_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Model Name: </div>
      <b-form-input v-model="model_name_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Tag: </div>
      <b-form-input v-model="tag_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="search-btn-container">
      <b-button class="search-btn" variant="primary" @click="on_search">Search</b-button>
    </div>
  </div>

  <ModelTable ref="model_table" />
</div>
</template>


<script>
import ModelTable from '@/components/ModelTable.vue'
import utils from '/src/utils.js';

export default {
  name: 'Models',
  components: {
    ModelTable,
  },
  data() {
    return {
      model_id_filter: utils.getCurrentParam("model_id_filter"),
      model_name_filter: utils.getCurrentParam("model_name_filter"),
      tag_filter: utils.getCurrentParam("tag_filter"),
    };
  },
  mounted() {
    let model_id_filter = utils.getCurrentParam("model_id_filter");
    let model_name_filter = utils.getCurrentParam("model_name_filter");
    let tag_filter = utils.getCurrentParam("tag_filter");

    if (model_id_filter || model_name_filter || tag_filter)
      this.$refs.model_table.load(model_id_filter, model_name_filter, tag_filter);
  },
  methods: {
    on_input_keydown: function() {
      if (event.which == 13)
        this.on_search();
    },
    on_search: function() {
      var params = new URLSearchParams();

      if (this.model_id_filter)
        params.set("model_id_filter", this.model_id_filter);

      if (this.model_name_filter)
        params.set("model_name_filter", this.model_name_filter);

      if (this.tag_filter)
        params.set("tag_filter", this.tag_filter);

      history.pushState(
        {},
        null,
        params.toString().length != 0 ? `/models?${params.toString()}` : "/models",
      )

      this.$refs.model_table.load(
        this.model_id_filter,
        this.model_name_filter,
        this.tag_filter,
      );
    }
  }
}
</script>


<style scoped>
.model_table {
    margin: 10px;
}
.loading_spinner {
    margin: 10px;
}
.filter_card {
    margin: 10px auto;
    padding-left: 200px;
    padding-right: 200px;
    margin-top: auto;
    margin-bottom: auto;
}
.filter_title {
    font-weight: bold;
    font-size: 18px;
    margin: 10px;
    width: 200px;
    height: 100%;
    line-height: 32px;
    text-align: left;
}
.filter_group {
    display: flex;
    height: 32px;
    margin: 10px;
}
.filter_key {
    width: 200px;
    height: 100%;
    line-height: 32px;
    text-align: left;
}
.search-btn-container {
    display: flex;
    justify-content: flex-end;
}
.search-btn {
    margin: 10px;
}
</style>
