<template>
  <div>
    <el-container>
      <el-header>
        <el-col :span="6">
          <el-input v-model="search_key" placeholder="请输入需要检索的电影名称"></el-input>
        </el-col>
        <el-col :span="1">
          <el-button icon="el-icon-search" type="warning" plain circle @click="search()"></el-button>
        </el-col>
        <el-col :span="10" class="header-text">电 影 列 表</el-col>
        <el-col :span="6">
          <el-button type="warning" @click="goToIndex"
                     style="float: right; margin-top: 10px;">用户退出</el-button>
        </el-col>
      </el-header>
      <el-container>
        <el-aside>
          <div class="boarding">
            <Boarding />
          </div>
        </el-aside>
        <el-main>
          <el-row v-for="(movie,index) in movieShowed" :key="index">
            <el-col :span="24">
              <MovieCard :detail="movie" />
            </el-col>
          </el-row>
          <div class="block">
            <el-pagination
              @current-change="handleCurrentChange"
              layout="prev, pager, next"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="totalMovie"
            ></el-pagination>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
  import MovieCard from "./MovieCard";
  import Boarding from "./Boarding";
  import axios from "axios";
  import Chart from "./Chart"
  export default {
    name: "MovieList",
    components: {
      MovieCard,
      Boarding,
      Chart
    },
    data() {
      return {
        movies: [],
        currentPage: 1,
        pageSize: 10,
        totalMovie: 0,
        search_key: "",
        oldSearch: "",
        genre: ""
      };
    },

    mounted: function() {
      this.search();
    },
    computed: {
      movieShowed: function() {
        return this.movies.slice(
          (this.currentPage - 1) * this.pageSize,
          this.currentPage * this.pageSize
        );
      }
    },
    methods: {
      handleCurrentChange(val) {
        this.currentPage = val;
      },
      searchTitle(movieTitle) {
        this.search = movieTitle;
      },
      search:function() {
        axios
          .post(`/api/query_movie_list`, { start_from: 0, limitation: 200,search_key:this.search_key })
          .then(res => {
            this.movies = res.data;
            this.totalMovie = res.data.length;
          })
          .catch(res => {});
      },
      goToIndex() {
        this.$router.push({name: "index"})
      }
    }
  };
</script>

<style>
  #app {
    font-family: "Avenir", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #2c3e50;
  }

  ul {
    list-style-type: none;
    padding: 0;
  }

  li {
    display: inline-block;
    margin: 0 10px;
  }

  a {
    color: #42b983;
  }

  .el-header {
    background-color: RGB(84, 92, 100);
    color: white;
    text-align: center;
    line-height: 60px;
    font-size: 18px;
  }

  .header-text {
    font-size: 20px;
  }

  .el-aside {
    background-color: #D3DCE6;
    color: #333;
    text-align: center;
    line-height: 200px;
    width: 25%;
  }

  .el-main {
    background-color: #E9EEF3;
    color: #333;
    text-align: center;
    line-height: 130px;
  }

  body > .el-container {
    margin-bottom: 40px;
  }

  .el-container:nth-child(5) .el-aside,
  .el-container:nth-child(6) .el-aside {
    line-height: 260px;
  }

  .el-container:nth-child(7) .el-aside {
    line-height: 320px;
  }

  .block {
    float: right;
    padding-top: 15px;
  }

  .el-dropdown-link {
    cursor: pointer;
    color: white;
  }

  .el-icon-arrow-down {
    font-size: 12px;
  }

  .boarding {
    padding-left: 8px;
  }
</style>
