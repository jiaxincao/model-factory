<template>
  <b-modal ref="modal" :title="title" :size="size" centered>
    <div v-html="text" />
  </b-modal>
</template>

<script>
export default {
  name: "SimpleModal",
  props: {
  },
  data() {
    return {
      visible: false,
      title: "",
      text: "",
      size: "lg",
    }
  },
  methods: {
    hide() {
      // method for closing modal
      this.visible = false;
    },
    show(title, text, size="lg") {
      this.title = title;
      this.text = text;
      this.size = size;

      // confirm code will be here soon(TM)
      this.$refs.modal.show();
    }
  }
}
</script>

<style scoped>
</style>
