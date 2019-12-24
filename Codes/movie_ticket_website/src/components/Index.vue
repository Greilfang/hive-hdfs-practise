<template>
  <div>
    <el-container>
      <el-header>身份验证</el-header>
      <el-main>
        <el-button type="warning" round @click="goToMovieList">用户登陆</el-button>
        <br />
        <el-button type="warning" round @click="goToOrderList">管理员登陆</el-button>
      </el-main>
    </el-container>
  </div>
</template>

<script>
  export default {
    name: "OrderList",
    methods: {
      goToMovieList() {
        this.$router.push({name: "movie-list"})
      },
      goToOrderList() {
        this.$router.push({name: "order-list"})
      }
    }
  }
</script>

<style scoped>
  .el-header {
    background-color: RGB(84, 92, 100);
    color: white;
    font-size: 18px;
    text-align: center;
    line-height: 60px;
  }

  .el-main {
    background-color: #E9EEF3;
    color: #333;
    text-align: center;
    line-height: 130px;
  }
</style>
