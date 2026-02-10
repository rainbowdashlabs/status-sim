import { createApp } from 'vue'
import axios from 'axios';
import './style.css'
import App from './App.vue'
import { backendBaseUrl } from './config/backend';

axios.defaults.baseURL = backendBaseUrl;

createApp(App).mount('#app')
