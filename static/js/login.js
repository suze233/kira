var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        show_menu:false,
        username:'',
        password:'',
        remembered:'',
    },
    mounted(){
       
    },
    methods: {
        //显示下拉菜单
        show_menu_click:function(){
            this.show_menu = !this.show_menu ;
        },
        //检查用户名
        check_username:function () {
            
        },
        //检查密码
        check_mobile:function () {
            
        },
        //提交
        on_submit:function () {
            
        }
    }
});
