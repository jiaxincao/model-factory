<template>
<div v-show=show_component>
  <b-table id="model-table" perPage="20" :current-page="current_page" bordered :busy=table_busy :items="models_info" :fields="fields" label-sort-asc="" label-sort-desc="" :tbody-tr-class="rowClass" sort-desc sort-by="creation_timestamp" >
    <template #table-busy>
      <div class="text-center text-info my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>
    </template>

    <template #cell(metrics)="data" >
      <div class="model-metrics">
        <pre>{{ data.value }}</pre>
      </div>
    </template>

    <template #cell(actions)="row">
      <b-dropdown id="dropdown-1" text="Actions" variant="primary" right>
        <b-dropdown-item  @click="promote_model(row)">Promote</b-dropdown-item>
      </b-dropdown>
    </template>
  </b-table>

  <b-pagination class="pagination" v-show="show_pagination" v-model="current_page" :total-rows="model_number" :per-page="20" aria-controls="models-table" align="center" first-number last-number pills />

  <SimpleModal ref="simple_modal" />
</div>
</template>

<script>
import axios from 'axios';
import utils from '/src/utils.js';
import SimpleModal from '@/components/SimpleModal.vue'

export default {
  name: 'ModelTable',
  components: {
    SimpleModal,
  },
  data() {
    return {
      show_pagination: false,
      model_number: 0,
      current_page: 1,
      show_component: false,
      table_busy: false,
      models_info: [],
      fields: [
        {key: 'model_id', label: 'Model ID', tdClass: 'align-middle', sortable: true},
        {key: 'tags', label: 'Tags', tdClass: 'align-middle', sortable: true},
        {key: 'model_name', label: 'Model Name', tdClass: 'align-middle', sortable: true},
        {key: 'job_id', label: 'Job ID', tdClass: 'align-middle', sortable: true},
        {key: 'production', label: 'Production', tdClass: 'align-middle', sortable: true},
        {key: 'creation_timestamp', label: 'Creation Time', tdClass: 'align-middle', sortable: true},
        {key: 'metrics', label: 'Metrics', tdClass: 'left', sortable: true},
        {key: 'actions', label: 'Actions', tdClass: 'align-middle', sortable: true},
      ],
      action_title: undefined,
      action_content: undefined,
    }
  },
  methods: {
    rowClass: function(item) {
      if (item == null)
        return

      if (item.status == "succeeded")
        return 'table-success';
      else if (item.status == "failed")
        return 'table-danger';
      else if (item.status == "deleted")
        return 'table-secondary';
      else if (item.status == "pending")
        return 'table-warning';
      else if (item.status == "running")
        return 'table-info';
    },
    load: function(
      model_id_filter,
      model_name_filter,
      tag_filter,
    ) {
      this.show_component = true;

      const frontend_endpoint = utils.getFrontendEndpoint();

      this.show_pagination = false;
      this.table_busy = true;

      let model_filter = {
        tags: {"$nin": ["hide"]},
      }

      if (model_id_filter)
        model_filter["model_id"] = model_id_filter;

      if (model_name_filter)
        model_filter["model_name"] = model_name_filter;

      if (tag_filter)
        model_filter["tags"]["$in"] = [tag_filter];

      axios.post(
        `${frontend_endpoint}/list_models`,
        {
          model_filter: model_filter,
        }
      ).then(response => {
        console.log(response);

        let models_info = []

        for (let i = 0; i < response.data.length; i++)
        {
          models_info.push({
            model_id: response.data[i]["_id"],
            model_name: response.data[i]["model_name"],
            job_id: response.data[i]["job_id"],
            tags: response.data[i]["tags"] && response.data[i]["tags"].join(", "),
            creation_timestamp: utils.getTimeString(response.data[i]["timestamp"]),
            metrics: JSON.stringify(response.data[i]["metric"], null, 2),
          });
        }

        this.models_info = models_info;
        this.model_number = models_info.length;

        this.show_pagination = true;
        this.table_busy = false;
      }).catch(e => {
        console.log(e);
      })
    },
    promote_model: function(row) {
      console.log(row);

      const frontend_endpoint = utils.getFrontendEndpoint();

      axios.post(
        `${frontend_endpoint}/promote_model`,
        {
          model_id: row.item.model_id,
        }
      ).then(() => {
        this.$refs.simple_modal.show(
          "Promote Model",
          `Model ${row.item.model_id} has been promoted to production!`,
        )
      }).catch(e => {
        this.$refs.simple_modal.show(
          "Error",
          `Failed to promote model ${row.item.model_id}: ${e}`,
        )
      })
    },
  },
}
</script>

<style scoped>
.model-metrics {
    text-align: left;
}
</style>
