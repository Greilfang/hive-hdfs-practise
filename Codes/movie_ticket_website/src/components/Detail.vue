<template>
  <div>
    <el-container>
      <el-header>
        {{this.detail.title}}
        <el-button type="warning" style="float: right; margin-top: 10px;"
                   @click="goToMovieList">返回电影列表</el-button>
      </el-header>
      <el-main>
        <div class="container">
          <img :src="poster" :alt="title" @error="imgError()" class="poster" />
          <div style="flex: 1;">
            <div class="casts">
              <div>
                导演:
                <span v-for="(person, index) in directors" :key="index+100" class="director">
                  {{person.name}}
                  <a v-if="person!=directors[directors.length-1]" class="director">, </a>
                </span>
              </div>
              <div>
                编剧:
                <span v-for="(person, index) in writers" :key="index+1000">
                  {{person.name}}<a v-if="person!=writers[writers.length-1]" class="sep">, </a>
                </span>
              </div>
              <div>
                演员:
                <span v-for="(person, index) in casts" :key="index+1000">
                  {{person.name}}
                  <a v-if="person!=casts[casts.length-1]" class="sep">, </a>
                </span>
              </div>
            </div>
            <div class="check">
              上映日期:
              <span v-for="(date, index) in pubdate" :key="index" class="date">{{date}}</span>
              <div class="duration">
                片长: {{duration}}min
              </div>
              类型:
              <span v-for="(genre, index) in genres" :key="index+10" class="genre">{{genre}}</span>
              <div>
                制片国家/地区:
                <span v-for="(country, index) in countries" :key="index+110" class="genre">{{country}}</span>
              </div>
              <div>
                语言:
                <span v-for="(language, index) in languages" :key="index+120" class="genre">{{language}}</span>
              </div>
              <div style="color: #337ab7; font-weight: bold">
                票价: {{this.price}} 元
              </div>
            </div>
          </div>
          <div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="rate"
                  disabled
                  text-color="#ff9900"
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="score" :style="{'color':getScoreColor}">{{rating.average}}</span>
              <span class="rating-people">({{rating.rating_people}}人评分)</span>
            </div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="value5"
                  disabled
                  show-text
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  text-color="#ff9900"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="rating-people">{{rating.stars[0]}}%</span>
            </div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="value4"
                  disabled
                  show-text
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  text-color="#ff9900"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="rating-people">{{rating.stars[1]}}%</span>
            </div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="value3"
                  disabled
                  show-text
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  text-color="#F7BA2A"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="rating-people">{{rating.stars[2]}}%</span>
            </div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="value2"
                  disabled
                  show-text
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  text-color="#99A9BF"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="rating-people">{{rating.stars[3]}}%</span>
            </div>
            <div>
              <span class="rating">
                <el-rate
                  v-model="value1"
                  disabled
                  show-text
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                  text-color="#99A9BF"
                  score-template="{value}">
                </el-rate>
              </span>
              <span class="rating-people">{{rating.stars[4]}}%</span>
            </div>
          </div>
        </div>
        <div class="intro">
          <div class="intro-word">简介</div><br>
          <div>{{summary}}</div>
        </div>
        <div class="buy">
          <el-button type="primary" @click="openDialog">购 票</el-button>
          <el-dialog
            :visible.sync="dialogVisible"
            width="30%"
            :before-close="handleClose">
            <div style="height: 100px">
              <span>购 票 数 目</span>
              <el-input-number v-model="ticketNum" @change="handleChange" :min="1" :max="10" label="购票数目"></el-input-number>
            </div>
            <span slot="footer" class="dialog-footer">
                  <el-button @click="dialogVisible = false">取 消</el-button>
                  <el-button type="primary" @click="this.buyTicket">确 定</el-button>
                </span>
          </el-dialog>
        </div>
        <div class="review">
          <div class="review-word">评价</div><br>
          <div v-for="item in reviews" style="margin-bottom: 25px;">
            <div style="margin-top: 3px; margin-bottom: 6px;">
              <span style="color: rgb(0, 119, 34);">匿名用户{{item.review_id}}</span>
              &nbsp;
              <span style="color: #337ab7;">分数: {{item.ranking}}分</span>
            </div>
            <div>{{item.content}}</div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
  import axios from 'axios'

  export default {
    name: "Detail",
    data() {
      return {
        movies: [],
        detail: [],

        title: "",
        poster: "",
        directors: [],
        writers: [],
        casts: [],
        pubdate: [],
        duration: "",
        genres: [],
        countries: [],
        languages: [],

        rating: {
          average: 3,
          rating_people: 0,
          stars: []
        },
        rate: 3,
        value1: 1,
        value2: 2,
        value3: 3,
        value4: 4,
        value5: 5,

        summary: "",

        price: 0,
        dialogVisible: false,
        ticketNum: 1,

        reviews: []
      }
    },
    mounted: function() {
      axios.post(`/api/query_movie/${this.$route.params.id}`)
        .then((res) => {
          var data = res.data[0]
          this.title = data.information.title
          this.poster = data.information.poster
          this.directors = data.information.directors
          this.writers = data.information.writers
          this.casts = data.information.casts
          this.pubdate = JSON.parse(data.information.pubdate)
          this.duration = data.information.duration
          this.genres = data.information.genres
          this.countries = data.information.countries
          this.languages = data.information.languages
          this.rating = data.information.rating
          this.rate = parseFloat((parseFloat(data.information.rating.average)/2).toFixed(1))
          if(data.information.rating.average === "") {
            this.rate = 0
            this.rating.average = ""
            this.rating.rating_people = 0
            this.rating.stars = [0, 0, 0, 0, 0]
          }
          this.summary = data.information.summary
          this.price = data.information.price
          this.ticketNum = 1
          this.reviews = data.reviews
        })
        .catch(this.getJsonInfo())
      console.log("电影ID：" + this.$route.params.id)
    },
    methods: {
      getJsonInfo: function() {
        this.$http.options.emulateJSON = true
        this.$http.get('./static/films.json').then(function(response){
          this.movies = response.data
          this.detail = this.movies
            .filter((info) => {
              const text = Object.values(info._id).join('').toLowerCase()
              return text.search(this.$route.params.id) >= 0
            })[0]

          this.totalMovie = this.movies.length
          this.initFromNative()
        }).catch(function(response){
        })
      },
      initFromNative: function() {
        this.casts = this.detail.casts
        this.countries = this.detail.countries
        this.directors = this.detail.directors
        this.duration = this.detail.duration
        this.genres = this.detail.genres
        this.languages = this.detail.languages
        this.poster = this.detail.poster
        this.pubdate = this.detail.pubdate
        this.rating = this.detail.rating
        this.summary = this.detail.summary
        this.title = this.detail.title
        this.writers = this.detail.writers
        this.countries = this.detail.countries
        this.languages = this.detail.languages
        this.rate = parseFloat((parseFloat(this.detail.rating.average)/2).toFixed(1))
        if(this.detail.rating.average === "") {
          this.rate = 0
          this.rating.average = ""
          this.rating.rating_people = 0
          this.rating.stars = [0, 0, 0, 0, 0]
        }
        console.log(this.rate)
        console.log(this.rating)
      },
      imgError() {
        this.poster = require('../assets/LostSource.png')
      },
      goToMovieList() {
        this.$router.push({name: "movie-list"})
      },
      openDialog() {
        this.ticketNum = 1
        this.dialogVisible = true
      },
      handleClose(done) {
        this.$confirm('确认关闭？')
          .then(_ => {
            done()
          })
          .catch(_ => {})
      },
      handleChange(value) {
        console.log(value)
      },
      buyTicket() {
        axios.post(`/api/insert_order`,
          {
            'item': {
            'movie_id': this.$route.params.id,
            'movie_name': this.title,
            'price_sum': this.price * this.ticketNum,
            'movie_num': this.ticketNum
          }
        })
        this.dialogVisible = false
        this.$message({
          message: '购票成功',
          type: 'success'
        })
      }
    },
    computed: {
      getScoreColor() {
        if(this.rating.average > 7.9)
          return '#FF9900'
        else if(this.rating.average > 4)
          return '#F7BA2A'
        else
          return '#FF9900'
      }
    },
    watch: {
      '$route' (to, from) {
        this.$router.go(0)
      }
    },
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
    text-align: center;
    line-height: 130px;
  }

  .container {
    display: flex;
    padding: 10px;
    padding-left: 20%;
    padding-right: 20%;
    text-align: left;
    line-height: 1.6;
  }
  .poster {
    margin-right: 12px;
    flex-shrink: 0;
    width: 160px;
    height: 240px;
  }
  .check {
    font-size: 15px;
    opacity: 1;
    letter-spacing: 0.5px;
  }
  .genre {
    float: inherit
  }
  .genre::after {
    content: "  ";
    color: #ddd;
  }
  .duration::after {
    content: "  ";
    color: #ddd;
  }
  .score {
    color: #f7ba2a;
    font-size: 15px;
    opacity: 1;
  }
  .rating {
    display: inline-table
  }
  .rating-people {
    padding-left: 5px;
    font-size: 12px;
  }
  .casts {
    font-size: 16px;
    opacity: 1;
    font-weight: 400;
    letter-spacing: 0.5px;
  }
  .sep {
    color: black;
  }
  .director {
    color: black
  }
  .intro {
    opacity: 1;
    line-height: 1.4;
    letter-spacing: 0.5px;
    font-size: 14px;
    padding-top: 5px;
    word-break: break-all;
    padding-left: 20%;
    padding-right: 20%;
    text-align: left;
  }
  .intro-word {
    color: #337ab7;
    font-size: 20px;
  }
  .review {
    opacity: 1;
    line-height: 1.4;
    letter-spacing: 0.5px;
    font-size: 14px;
    padding-top: 5px;
    word-break: break-all;
    padding-left: 20%;
    padding-right: 20%;
    text-align: left;
  }
  .review-word {
    color: #337ab7;
    font-size: 20px;
  }
</style>
