
// import { createApp, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js'
import { createApp, ref } from './pkg/vue.esm-browser.js'

createApp({
  setup() {
    const cnt = ref(0)

    function add_cnt() {
      cnt.value += 1
    }

    return {cnt, add_cnt}
  },
  template: `<div @click="add_cnt">{{ cnt }}</div>`
}).mount('#app')
