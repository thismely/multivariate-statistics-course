import {createApp} from 'vue'
import {createPinia} from 'pinia'
import CourseApp from './CourseApp.vue'
import './style.css'
import './course.css'
createApp(CourseApp).use(createPinia()).mount('#app')
