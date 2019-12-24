<template>
  <div class="board">
    <el-col class="sub-header">口碑榜</el-col>
    <div class=boarding-list>
      <p v-for="(movie, index) in recommend_movies"
         :key="index" @click="selectMovie(movie)"
         class="title">{{movie.information.title}}</p>
    </div>
  </div>
</template>

<script>
  import axios from 'axios'
  export default {
    name: "Boarding",
    props: ["movieList"],
    data(){
      return {
        recommend_movies:[]
      }
    },
    mounted:function(){
      this.recommends();
    },
    methods: {
      selectMovie: function(movie) {
        console.log(movie)
        this.$router.push({name: "movie-detail", params: {id: movie.movie_id}})
      },
      recommends() {
        axios.post(`/api/recommend_movie_list`, {
          start_from: 0,
          limitation: 15
        })
          .then((res) => {
            this.recommend_movies=res.data
          })
      }
    }
  }
</script>

<style scoped>
  .board {
    -webkit-user-select: none
  }
  .sub-header {
    text-align: left;
    padding-left: 12px;
    padding-top: 25px;
    font-size: 20px;
    opacity: 1;
    line-height: 1.4;
    font-weight: 500;
    color: darkcyan
  }
  .boarding-list {
    opacity: 1;
    line-height: 1.4;
    font-weight: 500;
    text-align: left;
    float: left;
    padding: 12px;
  }
  .title {
    cursor: pointer;
  }
</style>
