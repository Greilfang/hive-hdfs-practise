<template>
  <div>
    <el-menu
      :default-active="activeIndex"
      mode="horizontal"
      @select="handleSelect"
      background-color="#545c64"
      text-color="#fff"
      active-text-color="#ffd04b"
      :router="true">
      <el-menu-item index="order-list" style="width: 20%; text-align: center;">订单查询</el-menu-item>
      <el-menu-item index="chart" style="width: 20%; text-align: center;">销售概况</el-menu-item>
      <el-button type="warning"
                 style="margin-top: 10px; margin-left: 48%; width: 10%;"
                 @click="goToIndex">管理员退出</el-button>
    </el-menu>
    <el-container>
      <el-main>
        <el-row>
          <el-select v-model="year">
            <el-option value="%" label="请选择"></el-option>
            <el-option v-for="item in years" v-bind:value="item">{{ item }}</el-option>
          </el-select>
          <span>年</span>
          <el-select v-model="month">
            <el-option value="%" label="请选择"></el-option>
            <el-option v-for="item in months" v-bind:value="item">{{ item }}</el-option>
          </el-select>
          <span>月</span>
          <el-select v-model="day">
            <el-option value="" label="请选择"></el-option>
            <el-option v-for="item in days" v-bind:value="item">{{ item }}</el-option>
          </el-select>
          <span>日</span>
          <el-button plain round @click="selectOrder()">筛选</el-button>
        </el-row>
        <el-table :data="orderTable" stripe style="width: 100%">
          <el-table-column prop="order_id" label="订单 ID" sortable min-width="120"></el-table-column>
          <el-table-column prop="movie_id" label="电影 ID" sortable min-width="120"></el-table-column>
          <el-table-column prop="movie_name" label="电影名称" sortable min-width="200"></el-table-column>
          <el-table-column prop="movie_num" label="购票数" sortable min-width="120"></el-table-column>
          <el-table-column prop="price_sum" label="总价" sortable min-width="120"></el-table-column>
          <el-table-column prop="create_time" label="创建时间" sortable min-width="200"></el-table-column>
        </el-table>
      </el-main>
    </el-container>
    <div v-if="has_more" class="load-more">
      <spin v-if="is_loading">
        <div>Loading...</div>
      </spin>
      <spin v-else>
        <div @click="generateData()">Load More...</div>
      </spin>
    </div>
    <div v-else class="no-more">No More</div>
  </div>
</template>

<script>
  import axios from "axios";

  export default {
    name: "OrderList",
    data() {
      return {
        activeIndex: "order-list",
        orderTable: [],
        start_from: 0,
        limitation: 10,
        has_more: true,
        is_loading: false,
        scroll_top: 0,
        years: [],
        months: [],
        days: [],
        year: "%",
        day: "",
        month: "%",
        date_str: "%-%-%"
      };
    },
    mounted: function() {
      for (var i = 1; i <= 12; ++i) {
        if (i < 10) {
          this.months.push("0" + i);
        } else {
          this.months.push("" + i);
        }
      }
      for (var i = 1; i <= 31; ++i) {
        if (i < 10) {
          this.days.push("0" + i);
        } else {
          this.days.push("" + i);
        }
      }
      var date=new Date()
      for (var i = 2015; i <= date.getFullYear(); ++i) {
        this.years.push("" + i);
      }

      this.generateData();
    },
    methods: {
      generateData: function() {
        this.is_loading = true;
        this.scroll_top = document.documentElement.scrollTop;
        axios
          .post(`/api/query_order_list`, {
            start_from: this.start_from,
            limitation: this.limitation,
            time_limitation: this.date_str
          })
          .then(res => {
            this.start_from += this.limitation;
            if (res.data.length == 0) {
              this.has_more = false;
            } else {
              this.has_more = true;
            }
            this.orderTable = this.orderTable.concat(res.data);
            this.is_loading = false;
          });
      },
      selectOrder: function() {
        this.date_str = this.year + "-" + this.month + "-" + this.day + "%";
        console.log(this.date_str);
        this.orderTable = [];
        this.start_from = 0;
        this.generateData();
      },
      handleSelect(key, keyPath) {
        console.log(key, keyPath);
        // this.$router.push({name: key})
      },
      goToIndex() {
        this.$router.push({name: "index"})
      }
    },
    updated: function() {
      this.$nextTick(function() {
        document.documentElement.scrollTop = this.scroll_top;
      });
    }
  };
</script>

<style scoped>
  .el-main {
    background-color: #e9eef3;
    color: #333;
    text-align: center;
    line-height: 100px;
  }
  .load-more {
    /* font-size: 30px;*/
    font-weight: bold;
    color: rgb(84, 92, 100);
    text-align: center;
    margin-bottom: 20px;
    border-radius: 10px;
    background-color: white;
    width: 100%;
  }

  .load-more:hover {
    cursor: pointer;
  }
  .no-more {
    width: 100%;
    text-align: center;
    margin-bottom: 20px;
    border-radius: 10px;
    font-weight: bold;
    color: #b9b9b9;
  }
</style>
