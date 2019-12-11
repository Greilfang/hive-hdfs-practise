<template>
  <div>
    <el-menu
      :default-active="activeIndex"
      mode="horizontal"
      @select="handleSelect"
      background-color="#545c64"
      text-color="#fff"
      active-text-color="#ffd04b"
      :router="true"
    >
      <el-menu-item index="order-list" style="width: 20%; text-align: center;">订单查询</el-menu-item>
      <el-menu-item index="chart" style="width: 20%; text-align: center;">销售概况</el-menu-item>
      <el-button
        type="warning"
        style="margin-top: 10px; margin-left: 48%; width: 10%;"
        @click="goToIndex"
      >管理员退出</el-button>
    </el-menu>
    <el-container>
      <el-main style="text-align:center">
        <el-row style="left:25%">
          <div :id="id+0" v-bind:style="{height:height,width:'40%'}"></div>
        </el-row>
        <el-row style="left:25% ">
          <el-date-picker
            v-model="now_year"
            type="year"
            placeholder="请选择"
            value-format="yyyy"
            size="small"
            v-bind:picker-options="year_picker_options"
            @change="create_year_charts"
            :editable="false"
          ></el-date-picker>
          <div :id="id+1" v-bind:style="{height:height,width:'40%'}"></div>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
  import echarts from "echarts";
  import axios from "axios";

  export default {
    name: "Chart",
    data() {
      return {
        activeIndex: "chart",
        years: [],
        months: [
          "01",
          "02",
          "03",
          "04",
          "05",
          "06",
          "07",
          "08",
          "09",
          "10",
          "11",
          "12"
        ],
        orders: [],
        now_year: "2015",
        sale_values_one_year: {},
        id: "chart",
        width: "800px",
        height: "600px",
        year_picker_options:null
      };
    },
    mounted: function() {
      var _this = this;
      this.year_picker_options = {
        disabledDate(time) {
          return time.getFullYear() < 2015 || time > Date.now();
        }
      };
      var date = new Date();
      for (var i = 2015; i <= date.getFullYear(); ++i) {
        this.years.push(i);
      }
      this.init();
      axios
        .post("/api/query_order_list", {
          start_from: 0,
          limitation: Number.MAX_SAFE_INTEGER
        })
        .then(res => {
          this.orders = res.data;

          for (var k = 0; k < this.years.length; ++k) {
            var tmp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            for (var i = 0; i < this.orders.length; ++i) {
              for (var j = 0; j < 12; ++j) {
                if (
                  this.orders[i].create_time.indexOf(
                    this.years[k] + "-" + this.months[j]
                  ) != -1
                ) {
                  tmp[j] += this.orders[i].price_sum;
                  break;
                }
              }
            }
            this.sale_values_one_year[this.years[k]] = tmp;
          }

          this.create_pie_chart();
          this.create_year_charts();
        });
    },
    methods: {
      init: function() {
        var myChart = echarts.init(document.getElementById(this.id + "1"));
        // 绘制图表
        myChart.setOption({
          title: { text: "XXXX年销售情况", x: "center", y: "top" },
          tooltip: {},
          xAxis: {
            data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
          },
          yAxis: {},
          series: [
            {
              name: "销售额",
              type: "bar",
              data: []
            }
          ],
          grid: {}
        });
        myChart.showLoading();
        myChart = echarts.init(document.getElementById(this.id + "0"));
        // 绘制图表
        myChart.setOption({
          title: { text: "各年销售情况", x: "center", y: "top" },
          series: [
            {
              name: "销售额",
              type: "pie",
              data: []
            }
          ]
        });
        myChart.showLoading();
      },
      create_year_charts: function() {
        var max_v = 0;
        for (var i = 0; i < 12; ++i) {
          if (max_v < this.sale_values_one_year[this.now_year][i]) {
            max_v = this.sale_values_one_year[this.now_year][i];
          }
        }
        var y_values = [];
        for (var i = 0; i < 8; ++i) {
          y_values.push((max_v / 6) * i);
        }
        let myChart = echarts.init(document.getElementById(this.id + "1"));
        myChart.hideLoading();
        // 绘制图表
        myChart.setOption({
          title: { text: this.now_year + "销售情况", x: "center", y: "top" },
          tooltip: {},
          xAxis: {
            data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
          },
          yAxis: {},
          series: [
            {
              name: "销售额",
              type: "bar",
              data: this.sale_values_one_year[this.now_year]
            }
          ]
        });
      },
      create_pie_chart: function() {
        var pie_data = [];
        for (var i = 0; i < this.years.length; ++i) {
          var value = 0;
          for (var j = 0; j < 12; ++j) {
            value += this.sale_values_one_year[this.years[i]][j];
          }
          pie_data.push({ name: this.years[i], value: value });
        }
        let myChart = echarts.init(document.getElementById(this.id + "0"));
        myChart.hideLoading();
        // 绘制图表
        myChart.setOption({
          title: { text: "各年销售情况", x: "center", y: "top" },
          tooltip: {
            formatter: function(params) {
              var str = "";
              str += "年份: " + params.name + "<br/>";
              str += "销售额: " + Number(params.value).toFixed(1);
              return str;
            }
          },
          series: [
            {
              name: "销售额",
              type: "pie",
              data: pie_data,
              label: {
                show: true,
                formatter: "{b} : ({d}%)"
              },
              labelLine: { show: true }
            }
          ]
        });
      },
      handleSelect(key, keyPath) {
        console.log(key, keyPath);
        // this.$router.push({name: key})
      },
      goToIndex() {
        this.$router.push({ name: "index" });
      }
    }
  };
</script>
