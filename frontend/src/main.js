
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import piniaPersistedState from 'pinia-plugin-persistedstate'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'

import ConfirmDialog from 'primevue/confirmdialog'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'

import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog' 

import App from './App.vue'
import router from './router'

import 'primevue/resources/themes/saga-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import './static/main.css'
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import i18n from './locales/loader-final.js'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPersistedState)

app.use(pinia)
app.use(router)
app.use(PrimeVue)
app.use(i18n)
app.use(ConfirmationService)

app.component('InputText', InputText)
app.component('Button', Button)
app.component('Dropdown', Dropdown)
app.component('ConfirmDialog', ConfirmDialog)
app.component('Dialog', Dialog)
app.directive('tooltip', Tooltip)
app.use(ToastService)

app.mount('#app')
