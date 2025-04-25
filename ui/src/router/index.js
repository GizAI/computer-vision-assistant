import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/project/:id",
      name: "project",
      component: HomeView,
      props: true,
    },
    {
      // Redirect all other routes to home
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
});

export default router;
