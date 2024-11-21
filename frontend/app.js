
import { createApp, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js'
// import { createApp, ref } from './pkg/vue.esm-browser.js'

createApp({
  setup() {
    const count = ref(0)

    return {count}
  },
  template: `<div>Count is: {{ count }}</div>`
}).mount('#app')
