const routers = [
  {
    path: "/index",
    name: "index",
    component: (resolve) => require(['../components/Index.vue'], resolve)
  },
  {
    path: "/movie-list",
    name: "movie-list",
    component: (resolve) => require(['../components/MovieList.vue'], resolve)
  },
  {
    path: "/movie-detail/:id",
    name: "movie-detail",
    component: (resolve) => require(['../components/Detail.vue'], resolve)
  },
  {
    path: "/order-list",
    name: "order-list",
    component: (resolve) => require(['../components/OrderList.vue'], resolve)
  },
  {
    path: "/chart",
    name: "chart",
    component: (resolve) => require(['../components/Chart.vue'], resolve)
  },
  {
    path: "/",
    redirect: "index"
  },
]
export default routers
