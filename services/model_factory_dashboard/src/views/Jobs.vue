<template>
<div>

  <div class="filter_card">
    <div class="filter_title">
      Job Filters:
    </div>
    <div class="filter_group">
      <div class="filter_key" >Job ID: </div>
      <b-form-input v-model="job_id_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Pipeline Name: </div>
      <b-form-input v-model="pipeline_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Operator ID: </div>
      <b-form-input v-model="operator_id_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Tag: </div>
      <b-form-input v-model="tag_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Pool: </div>
      <b-form-input v-model="pool_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Owner: </div>
      <b-form-input v-model="owner_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="filter_group">
      <div class="filter_key" >Status: </div>
      <b-form-input v-model="status_filter" @keydown.native="on_input_keydown" />
    </div>
    <div class="search-btn-container">
      <b-button class="search-btn" variant="primary" @click="on_search">Search</b-button>
    </div>

  </div>

  <JobTable ref="job_table" />
</div>
</template>

<script>
import JobTable from '@/components/JobTable.vue'
import utils from '/src/utils.js';

export default {
  name: 'Jobs',
  components: {
    JobTable,
  },
  data() {
    return {
      job_id_filter: utils.getCurrentParam("job_id_filter"),
      pipeline_filter: utils.getCurrentParam("pipeline_filter"),
      operator_id_filter: utils.getCurrentParam("operator_id_filter"),
      pool_filter: utils.getCurrentParam("pool_filter"),
      tag_filter: utils.getCurrentParam("tag_filter"),
      owner_filter: utils.getCurrentParam("owner_filter"),
      status_filter: utils.getCurrentParam("status_filter"),
    };
  },
  mounted(){
    let job_id_filter = utils.getCurrentParam("job_id_filter");
    let pipeline_filter = utils.getCurrentParam("pipeline_filter");
    let operator_id_filter = utils.getCurrentParam("operator_id_filter");
    let pool_filter = utils.getCurrentParam("pool_filter");
    let tag_filter = utils.getCurrentParam("tag_filter");
    let owner_filter = utils.getCurrentParam("owner_filter");
    let status_filter = utils.getCurrentParam("status_filter");

    if (job_id_filter || pipeline_filter || operator_id_filter || pool_filter || tag_filter || owner_filter || status_filter)
      this.$refs.job_table.load(job_id_filter, pipeline_filter, operator_id_filter, pool_filter, tag_filter, owner_filter, status_filter);
  },
  methods: {
    on_input_keydown: function() {
      if (event.which == 13)
        this.on_search();
    },
    on_search: function() {
      var params = new URLSearchParams();

      if (this.job_id_filter)
        params.set("job_id_filter", this.job_id_filter);

      if (this.pipeline_filter)
        params.set("pipeline_filter", this.pipeline_filter);

      if (this.operator_id_filter)
        params.set("operator_id_filter", this.operator_id_filter);

      if (this.pool_filter)
        params.set("pool_filter", this.pool_filter);

      if (this.tag_filter)
        params.set("tag_filter", this.tag_filter);

      if (this.owner_filter)
        params.set("owner_filter", this.owner_filter);

      if (this.status_filter)
        params.set("status_filter", this.status_filter);

      history.pushState(
        {},
        null,
        params.toString().length != 0 ? `/jobs?${params.toString()}` : "/jobs",
      )

      this.$refs.job_table.load(
        this.job_id_filter,
        this.pipeline_filter,
        this.operator_id_filter,
        this.pool_filter,
        this.tag_filter,
        this.owner_filter,
        this.status_filter,
      );
    }
  }
}
</script>


<style scoped>
.job_table {
    margin: 10px;
}
.loading_spinner {
    margin: 10px;
}
.filter_card {
    padding-left: 200px;
    padding-right: 200px;
    margin-top: auto;
    margin-bottom: auto;
    width: 100%;
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
