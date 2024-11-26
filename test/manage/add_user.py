from dao.manage_dao import add_manage_user

users = ['10200fmc@sina.com', '1509658229@qq.com', '151423788@qq.com', '18870243977@163.com', '2244371386@qq.com',
         '2872265068@qq.com',
         '3046980100@qq.com', '307226281@qq.com', '419221492@qq.com', '546887681@qq.com', '70532865@qq.com',
         '708925918@qq.com',
         '994155725@qq.com', 'a731240874@163.com', 'castorj561@gmail.com', 'david.qi@talentechgroup.com',
         'graciawila16@gmail.com',
         'Jianeyen@163.com', 'lemon.dai@nstarts.com', 'lin523928805@gmail.com', 'lucina@remoly.net', 'nan0618x@163.com',
         'Olivia02031027@gmail.com',
         'oscar.huang@hiredchina.com', 'oskahuang@foxmail.com', 'songqiang51886@163.com', 'trisha_huang@126.com',
         'xianf14@lzu.edu.cn', 'zhuziheng1017@gmail.com']

if __name__ == "__main__":
    manage_id = "clement.hu689@gmail.com"
    for user_id in users:
        add_manage_user(manage_id, user_id)
