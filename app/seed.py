from flask import current_app

from .extensions import db
from .models import (
    Admin,
    DietMeal,
    DietTemplate,
    Equipment,
    EquipmentCategory,
    KnowledgeArticle,
    KnowledgeCategory,
    KnowledgeTip,
)


def seed_database():
    """写入演示数据，使用 count 做幂等判断，可重复执行。"""
    _seed_admin()
    _seed_equipment()
    _seed_knowledge()
    _seed_diet()
    db.session.commit()


def _seed_admin():
    username = current_app.config["ADMIN_USERNAME"]
    if Admin.query.filter_by(username=username).first():
        return
    admin = Admin(username=username, display_name="校园健身房管理员")
    admin.set_password(current_app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.flush()


def _seed_equipment():
    if EquipmentCategory.query.count() > 0:
        return

    category_rows = [
        ("胸部", "chest", "胸大肌、胸小肌及上肢推举训练", 10),
        ("肱二头肌", "biceps", "肘关节屈曲与手臂前侧训练", 20),
        ("肱三头肌", "triceps", "手臂后侧伸肘力量训练", 30),
        ("背部", "back", "背阔肌、斜方肌与菱形肌训练", 40),
        ("肩部", "shoulders", "三角肌与肩袖稳定训练", 50),
        ("臀腿", "glutes-legs", "臀大肌、股四头肌与腘绳肌训练", 60),
        ("核心", "core", "腹部、腰背与躯干稳定训练", 70),
        ("有氧", "cardio", "心肺耐力与热量消耗训练", 80),
    ]
    categories = {}
    for name, slug, description, order in category_rows:
        category = EquipmentCategory(
            name=name, slug=slug, description=description, sort_order=order
        )
        db.session.add(category)
        db.session.flush()
        categories[name] = category

    # name, category, description, action, force, mistakes, sets, reps, rest
    equipment_rows = [
        ("杠铃卧推", "胸部", "训练胸大肌、肱三头肌和三角肌前束的复合动作。", "肩胛后缩下沉，杠铃下放至胸部中下缘，前臂垂直地面后推起。", "保持胸腔抬起，用胸肌把上臂向中间夹合。", "手腕后折、耸肩、臀部离凳、杠铃砸胸。", 4, "8-10", 90),
        ("坐姿推胸器", "胸部", "轨迹固定的胸部推举器械，适合初学者。", "座椅高度让握把与胸部中段齐平，背部贴紧靠垫。", "回程控制两秒，主动收缩胸大肌。", "座椅不合适、耸肩、回程过快。", 3, "10-12", 75),
        ("哑铃弯举", "肱二头肌", "训练肱二头肌和抓握能力的基础动作。", "上臂贴近身体，屈肘并逐渐旋转前臂至掌心向上。", "固定上臂，不要用腰部摆动借力。", "身体后仰、肘部前后移动、下放过快。", 3, "10-12", 60),
        ("牧师凳弯举", "肱二头肌", "通过斜托固定上臂，突出肱二头肌刺激。", "腋窝贴近斜托，肘部与器械转轴对齐。", "肩部放松，用肱二头肌完成屈肘。", "底部弹震、只做半程、肩部前移。", 3, "10-12", 60),
        ("绳索下压", "肱三头肌", "龙门架绳索动作，阻力曲线平滑。", "上臂固定在身体两侧，伸直肘关节并分开绳索。", "肘部靠近身体，末端主动收缩。", "肘部外展、肩部代偿、身体摆动。", 3, "12-15", 60),
        ("双杠臂屈伸", "肱三头肌", "自重复合动作，训练肱三头肌和肩部稳定。", "肩胛下沉，屈肘下降至舒适范围后推起。", "躯干相对直立，全程控制肩部稳定。", "下降过深、耸肩、身体晃动。", 3, "6-10", 75),
        ("高位下拉", "背部", "主要刺激背阔肌和大圆肌。", "先下沉肩胛，再把横杆拉向上胸，回程充分拉长背阔肌。", "想象肘部向下移动，不只用手拉杆。", "大幅后仰、耸肩、拉到颈后。", 4, "10-12", 75),
        ("坐姿划船", "背部", "训练中背部厚度、背阔肌和肱二头肌。", "保持脊柱中立，先收肩胛再拉向腹部。", "肘部贴近身体，动作末端停顿。", "腰部屈伸、耸肩、只用手臂。", 4, "10-12", 75),
        ("哑铃推举", "肩部", "训练三角肌前束与中束。", "背部贴垫，哑铃从肩部两侧向上推举。", "肋骨下沉，核心收紧，避免腰椎反弓。", "腰部离垫、耸肩、下放过低。", 3, "8-12", 75),
        ("反向蝴蝶机飞鸟", "肩部", "训练三角肌后束和上背部。", "胸部贴垫，肘微屈向两侧展开后合拢。", "保持肘部高度，末端主动收缩后束。", "耸肩、甩动手臂、胸部离开靠垫。", 3, "12-15", 60),
        ("史密斯深蹲", "臀腿", "固定轨迹深蹲，重点训练股四头肌和臀大肌。", "屈髋屈膝下蹲至大腿接近平行，再蹬地站起。", "膝盖方向与脚尖一致，脚掌均匀发力。", "膝盖内扣、脚跟离地、腰部过度前倾。", 4, "8-10", 90),
        ("腿举机", "臀腿", "下肢复合训练器械，刺激股四头肌和臀部。", "背部与臀部贴垫，下放后蹬起但不锁死膝盖。", "膝盖沿脚尖方向运动，骨盆保持稳定。", "膝盖锁死、下放过深、膝盖内扣。", 4, "10-12", 90),
        ("悬垂举腿", "核心", "悬垂状态下训练腹部和髋屈肌。", "稳定肩胛，用腹部卷动骨盆抬腿。", "避免摆腿惯性，末端主动收缩腹肌。", "身体摇摆、只抬大腿、下放失控。", 3, "8-12", 60),
        ("罗马椅卷腹", "核心", "在罗马椅上进行脊柱屈曲训练。", "固定双脚，从胸椎开始逐节卷起。", "用腹部缩短躯干距离，不要折叠髋部。", "拉扯颈部、幅度过大、下落过快。", 3, "12-15", 45),
        ("跑步机", "有氧", "用于热身、心肺耐力和热量消耗。", "自然直立，脚落在身体重心下方，不要抓扶手。", "保持均匀呼吸和稳定步频。", "直接高速、结束不减速、身体后仰。", 1, "15-30 分钟", 0),
        ("划船机", "有氧", "全身参与的低冲击有氧器械。", "按腿、髋、手顺序拉桨，按手、髋、腿顺序回程。", "蹬腿是主要动力来源，保持节奏稳定。", "只用手臂、含胸驼背、膝盖内扣。", 1, "10-20 分钟", 0),
    ]

    for index, row in enumerate(equipment_rows, start=1):
        name, category_name, description, action, force, mistakes, sets, reps, rest = row
        equipment = Equipment(
            category_id=categories[category_name].id,
            name=name,
            cover_url=f"https://placehold.co/750x420/0f172a/ffffff?text=Equipment+{index}",
            image_urls=[f"https://placehold.co/750x420/0f172a/ffffff?text=Equipment+{index}"],
            description=description,
            action_key_points=action,
            force_points=force,
            common_mistakes=mistakes,
            video_url=f"https://www.douyin.com/video/placeholder-{index}",
            recommended_sets=sets,
            recommended_reps=reps,
            rest_seconds=rest,
            sort_order=index * 10,
        )
        db.session.add(equipment)


def _seed_knowledge():
    if KnowledgeCategory.query.count() == 0:
        rows = [
            ("训练入门", "training-basics", "🏋️"),
            ("增肌指南", "muscle-gain", "💪"),
            ("减脂塑形", "fat-loss", "🔥"),
            ("营养饮食", "nutrition", "🥗"),
            ("运动康复", "recovery", "🩹"),
        ]
        categories = {}
        for order, (name, slug, icon) in enumerate(rows, start=1):
            category = KnowledgeCategory(
                name=name, slug=slug, icon=icon, sort_order=order * 10
            )
            db.session.add(category)
            db.session.flush()
            categories[name] = category

        articles = [
            ("训练入门", "第一次去健身房应该练什么", "从低风险器械开始，先建立动作稳定。", "热身 5-10 分钟后，选择 3-5 个固定器械，每个动作做 2-3 组、每组 10-12 次。重量以动作不变形为准。"),
            ("增肌指南", "增肌训练的三个基本条件", "渐进超负荷、蛋白质和睡眠缺一不可。", "记录训练重量和次数，在动作标准前提下逐步增加负荷。每天每公斤体重可摄入 1.6-2.2 克蛋白质。"),
            ("减脂塑形", "减脂期为什么也要做力量训练", "力量训练帮助保留肌肉。", "每周安排 2-4 次力量训练，配合有氧和日常活动。减脂速度以每周 0.3%-1% 体重为宜。"),
            ("营养饮食", "健身前后怎么吃更合适", "训练前补充易消化碳水。", "训练前 1-2 小时可吃香蕉、燕麦，训练后正常进食。全天总热量和蛋白质比单次进食时间更重要。"),
            ("运动康复", "肌肉酸痛还能继续练吗", "轻度酸痛可降低强度。", "若出现尖锐疼痛、关节痛、肿胀或明显无力，应停止训练并咨询专业人员。"),
        ]
        for index, (category_name, title, summary, content) in enumerate(articles, start=1):
            db.session.add(
                KnowledgeArticle(
                    category_id=categories[category_name].id,
                    title=title,
                    summary=summary,
                    content=content,
                    cover_url=f"https://placehold.co/750x420/png?text=Knowledge+{index}",
                    view_count=index * 12,
                )
            )

    if KnowledgeTip.query.count() == 0:
        tips = [
            "训练重量不是越大越好，标准动作优先。",
            "力量训练组间通常休息 45-120 秒。",
            "睡眠不足会降低训练表现和恢复速度。",
            "先完成大肌群复合动作，再做孤立动作。",
            "减脂核心是长期稳定的热量缺口。",
            "增肌需要蛋白质、碳水和总热量共同支持。",
            "出现尖锐疼痛时应立即停止动作。",
        ]
        db.session.add_all([KnowledgeTip(content=item) for item in tips])


def _seed_diet():
    if DietTemplate.query.count() > 0:
        return

    templates = [
        ("增肌通用一日方案", "muscle_gain", None, None, 2600, "蛋白质分配到三餐，每餐约 30-40 克。", [
            ("breakfast", ["全麦面包 2 片", "鸡蛋 2 个", "牛奶 300ml", "香蕉 1 根"], 650),
            ("lunch", ["米饭 250g", "鸡胸肉 180g", "西兰花 200g"], 950),
            ("dinner", ["红薯 250g", "牛肉 150g", "混合蔬菜 250g"], 1000),
        ]),
        ("减脂通用一日方案", "fat_loss", None, None, 1800, "保持热量缺口，优先高蛋白、高纤维和少油烹饪。", [
            ("breakfast", ["无糖酸奶 250g", "燕麦 40g", "鸡蛋 1 个"], 420),
            ("lunch", ["杂粮饭 150g", "鸡胸肉 160g", "绿叶蔬菜 300g"], 650),
            ("dinner", ["玉米 1 根", "虾仁 180g", "菌菇蔬菜 300g"], 730),
        ]),
        ("塑形通用一日方案", "shaping", None, None, 2100, "每餐保证蛋白质和蔬菜，主食优先全谷物。", [
            ("breakfast", ["希腊酸奶 200g", "燕麦 45g", "鸡蛋 1 个"], 480),
            ("lunch", ["糙米饭 180g", "鸡胸肉 160g", "多彩蔬菜 300g"], 800),
            ("dinner", ["紫薯 180g", "鳕鱼 160g", "菠菜菌菇 300g"], 820),
        ]),
    ]
    for name, goal, gender, body_part, calories, tips, meals in templates:
        template = DietTemplate(
            name=name,
            fitness_goal=goal,
            gender=gender,
            body_part=body_part,
            meal_count=3,
            total_calories=calories,
            tips=tips,
        )
        db.session.add(template)
        db.session.flush()
        for order, (meal_type, foods, meal_calories) in enumerate(meals, start=1):
            db.session.add(
                DietMeal(
                    template_id=template.id,
                    meal_type=meal_type,
                    food_items=foods,
                    target_calories=meal_calories,
                    sort_order=order * 10,
                )
            )
