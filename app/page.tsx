"use client";

import { useMemo, useState } from "react";
import quotes from "./quotes.json";

type Field = "物理" | "化学" | "生命科学" | "数学" | "计算机" | "天文" | "医学" | "地球科学";

type Scientist = {
  id: string;
  month: number;
  day: number;
  name: string;
  latinName: string;
  years: string;
  field: Field;
  country: string;
  color: string;
  relation: string;
  tagline: string;
  story: string;
  contribution: string;
  fact: string;
};

const scientists: Scientist[] = [
  { id: "braille", month: 1, day: 4, name: "路易·布莱叶", latinName: "Louis Braille", years: "1809–1852", field: "生命科学", country: "法国", color: "coral", relation: "诞辰", tagline: "让文字可以被指尖阅读", story: "15 岁时，他把军用夜读密码改造成六点触摸书写法。", contribution: "布莱叶盲文", fact: "一格盲文最多由 6 个凸点构成。" },
  { id: "hawking", month: 1, day: 8, name: "史蒂芬·霍金", latinName: "Stephen Hawking", years: "1942–2018", field: "物理", country: "英国", color: "blue", relation: "诞辰", tagline: "把黑洞带进了可计算的宇宙", story: "他提出黑洞并非永远沉默，而会因量子效应缓慢辐射。", contribution: "霍金辐射", fact: "他的科普书《时间简史》曾在英国畅销书榜停留多年。" },
  { id: "franklin", month: 2, day: 4, name: "罗莎琳德·富兰克林", latinName: "Rosalind Franklin", years: "1920–1958", field: "化学", country: "英国", color: "violet", relation: "诞辰", tagline: "用一张衍射照片看见 DNA", story: "她用 X 射线衍射获得了著名的“照片 51”，为理解 DNA 的螺旋结构提供关键线索。", contribution: "DNA 结构研究", fact: "她也对煤、病毒结构做过扎实研究。" },
  { id: "darwin", month: 2, day: 12, name: "查尔斯·达尔文", latinName: "Charles Darwin", years: "1809–1882", field: "生命科学", country: "英国", color: "green", relation: "诞辰", tagline: "让生命拥有一条漫长的时间线", story: "从小猎犬号航行中的观察出发，他提出自然选择解释物种如何改变。", contribution: "进化论", fact: "小猎犬号航行历时近五年。" },
  { id: "galileo", month: 2, day: 15, name: "伽利略·伽利莱", latinName: "Galileo Galilei", years: "1564–1642", field: "天文", country: "意大利", color: "gold", relation: "诞辰", tagline: "用望远镜改变了天空", story: "他观测到木星卫星与金星盈亏，让天体不再只是哲学推论。", contribution: "系统天文观测", fact: "他发现的木星四颗大卫星今天仍以他命名。" },
  { id: "copernicus", month: 2, day: 19, name: "尼古拉·哥白尼", latinName: "Nicolaus Copernicus", years: "1473–1543", field: "天文", country: "波兰", color: "gold", relation: "诞辰", tagline: "让地球离开宇宙的中心", story: "他的日心说将行星的复杂运动放进一个更简洁的秩序。", contribution: "日心说", fact: "他的代表作在临终前后才正式出版。" },
  { id: "einstein", month: 3, day: 14, name: "阿尔伯特·爱因斯坦", latinName: "Albert Einstein", years: "1879–1955", field: "物理", country: "德国", color: "blue", relation: "诞辰", tagline: "重新定义时间、空间与重力", story: "1905 年，他接连发表多篇论文，推动了现代物理的转折。", contribution: "相对论与光电效应", fact: "GPS 的高精度定位需要修正相对论造成的时间差。" },
  { id: "curie", month: 11, day: 7, name: "玛丽·居里", latinName: "Marie Curie", years: "1867–1934", field: "物理", country: "波兰 / 法国", color: "violet", relation: "诞辰", tagline: "在微光里发现两种新元素", story: "她与皮埃尔·居里从沥青铀矿残渣中分离并研究放射性。", contribution: "放射性研究", fact: "她是首位获得诺贝尔奖的女性，也是首位两获诺奖的人。" },
  { id: "lamarr", month: 11, day: 9, name: "海蒂·拉玛", latinName: "Hedy Lamarr", years: "1914–2000", field: "计算机", country: "奥地利 / 美国", color: "coral", relation: "诞辰", tagline: "在银幕之外，构想通信的跳频", story: "她与乔治·安泰尔提出跳频通信构想，为现代无线通信的发展留下重要灵感。", contribution: "跳频通信构想", fact: "她同时是一位知名电影演员与发明者。" },
  { id: "nobel-prize-day", month: 12, day: 10, name: "诺贝尔奖日", latinName: "Nobel Prize Day", years: "1901–至今", field: "医学", country: "瑞典", color: "gold", relation: "颁奖日", tagline: "让突破被世界看见", story: "诺贝尔奖通常在 12 月 10 日颁发，纪念阿尔弗雷德·诺贝尔逝世日。", contribution: "跨学科科学奖项", fact: "和平奖在奥斯陆颁发，其他奖项在斯德哥尔摩。" },
  { id: "leonardo", month: 4, day: 15, name: "列奥纳多·达·芬奇", latinName: "Leonardo da Vinci", years: "1452–1519", field: "地球科学", country: "意大利", color: "coral", relation: "诞辰", tagline: "把观察变成了跨学科的笔记", story: "从人体解剖到水流、飞行与机械，他用图像记录对自然的好奇。", contribution: "科学观察与工程手稿", fact: "他的手稿常以镜像书写。" },
  { id: "nightingale", month: 5, day: 12, name: "弗洛伦斯·南丁格尔", latinName: "Florence Nightingale", years: "1820–1910", field: "医学", country: "英国", color: "green", relation: "诞辰", tagline: "用数据让医院变得更安全", story: "她将战地医院的死亡原因制成醒目的统计图，推动卫生改革。", contribution: "现代护理与卫生统计", fact: "她的极坐标图是数据可视化史上的经典案例。" },
  { id: "turing", month: 6, day: 23, name: "艾伦·图灵", latinName: "Alan Turing", years: "1912–1954", field: "计算机", country: "英国", color: "blue", relation: "诞辰", tagline: "在纸上发明一台通用计算机", story: "他的抽象计算模型告诉我们：哪些问题能被算法解决，哪些不能。", contribution: "图灵机与计算理论", fact: "图灵测试至今仍是人工智能讨论中的重要概念。" },
  { id: "goeppert", month: 6, day: 28, name: "玛丽亚·格佩特-梅耶", latinName: "Maria Goeppert-Mayer", years: "1906–1972", field: "物理", country: "德国 / 美国", color: "violet", relation: "诞辰", tagline: "解释原子核为何拥有“魔数”", story: "她提出核壳层模型，说明某些核子数为何格外稳定。", contribution: "核壳层模型", fact: "她是第二位获得诺贝尔物理学奖的女性。" },
  { id: "leibniz", month: 7, day: 1, name: "戈特弗里德·莱布尼茨", latinName: "G. W. Leibniz", years: "1646–1716", field: "数学", country: "德国", color: "gold", relation: "诞辰", tagline: "把变化写成一门语言", story: "他与牛顿各自发展微积分，并系统使用了至今常见的积分符号。", contribution: "微积分记号", fact: "二进制思想也曾在他的著作中被清晰阐述。" },
  { id: "bell", month: 7, day: 15, name: "乔斯琳·贝尔·伯内尔", latinName: "Jocelyn Bell Burnell", years: "1943–", field: "天文", country: "英国", color: "violet", relation: "诞辰", tagline: "在噪声中听见脉冲星", story: "作为研究生，她在射电图纸上注意到规律脉冲，开启脉冲星发现。", contribution: "脉冲星发现", fact: "她将一笔大奖奖金捐出，用于支持少数群体进入物理学。" },
  { id: "noether", month: 7, day: 29, name: "埃米·诺特", latinName: "Emmy Noether", years: "1882–1935", field: "数学", country: "德国", color: "coral", relation: "诞辰", tagline: "每一种对称，背后都有守恒", story: "她证明了物理定律的连续对称性与守恒定律之间的深刻联系。", contribution: "诺特定理", fact: "时间平移对称对应能量守恒。" },
  { id: "schrodinger", month: 8, day: 12, name: "埃尔温·薛定谔", latinName: "Erwin Schrödinger", years: "1887–1961", field: "物理", country: "奥地利", color: "blue", relation: "诞辰", tagline: "用方程描述微观世界的波", story: "薛定谔方程成为量子力学的基础工具，描述量子态如何随时间演化。", contribution: "薛定谔方程", fact: "“薛定谔的猫”原本是他用来讨论量子解释的思想实验。" },
  { id: "broglie", month: 8, day: 15, name: "路易·德布罗意", latinName: "Louis de Broglie", years: "1892–1987", field: "物理", country: "法国", color: "blue", relation: "诞辰", tagline: "提出物质也有波的一面", story: "他大胆提出电子等粒子具有波动性，后来被实验验证。", contribution: "物质波", fact: "电子显微镜正是利用电子的波动性质提高分辨率。" },
  { id: "lavoisier", month: 8, day: 26, name: "安托万·拉瓦锡", latinName: "Antoine Lavoisier", years: "1743–1794", field: "化学", country: "法国", color: "green", relation: "诞辰", tagline: "把称量带进化学实验室", story: "他严谨测量反应前后的质量，推动质量守恒思想与现代化学命名。", contribution: "质量守恒与化学命名", fact: "他帮助确认氧在燃烧中的作用。" },
  { id: "lovelace", month: 12, day: 10, name: "艾达·洛芙莱斯", latinName: "Ada Lovelace", years: "1815–1852", field: "计算机", country: "英国", color: "coral", relation: "算法纪念", tagline: "想象机器不只会算数", story: "她在分析机笔记中写下了可执行步骤，并预见通用计算机可处理符号与音乐。", contribution: "早期程序思想", fact: "Ada 语言以她的名字命名。" },
  { id: "rutherford", month: 10, day: 30, name: "欧内斯特·卢瑟福", latinName: "Ernest Rutherford", years: "1871–1937", field: "物理", country: "新西兰 / 英国", color: "gold", relation: "诞辰", tagline: "看见原子内部几乎全是空旷", story: "金箔散射实验让原子核模型诞生，改变了人们对物质内部的想象。", contribution: "原子核模型", fact: "他曾说自己研究的不是物理，而是炼金术。" },
  { id: "cajal", month: 5, day: 1, name: "圣地亚哥·拉蒙-卡哈尔", latinName: "Santiago Ramón y Cajal", years: "1852–1934", field: "医学", country: "西班牙", color: "violet", relation: "诞辰", tagline: "画出神经元彼此独立的世界", story: "他借助染色技术描绘神经细胞，奠定了神经元学说。", contribution: "神经元学说", fact: "他的神经系统手绘图兼具科学与艺术价值。" },
  { id: "carson", month: 5, day: 27, name: "蕾切尔·卡森", latinName: "Rachel Carson", years: "1907–1964", field: "地球科学", country: "美国", color: "green", relation: "诞辰", tagline: "让生态系统进入公共讨论", story: "《寂静的春天》提醒公众关注农药对鸟类、生态与健康的连锁影响。", contribution: "环境科学传播", fact: "她早年曾在美国渔业机构从事海洋生物写作。" },
  { id: "mendel", month: 7, day: 20, name: "格雷戈尔·孟德尔", latinName: "Gregor Mendel", years: "1822–1884", field: "生命科学", country: "奥地利", color: "green", relation: "诞辰", tagline: "从豌豆中读出遗传规律", story: "长期的豌豆杂交实验让他提出遗传因子分离与组合的规律。", contribution: "遗传定律", fact: "孟德尔的工作在发表数十年后才被广泛重新发现。" },
  { id: "hopper", month: 12, day: 9, name: "格蕾丝·霍珀", latinName: "Grace Hopper", years: "1906–1992", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "让程序更接近人类语言", story: "她推动编译器与高级编程语言发展，帮助计算机走出机器码的围墙。", contribution: "编译器与 COBOL", fact: "“debug”一词的著名轶事与她团队处理继电器飞蛾有关。" },
  { id: "goodall", month: 4, day: 3, name: "简·古道尔", latinName: "Jane Goodall", years: "1934–", field: "生命科学", country: "英国", color: "gold", relation: "诞辰", tagline: "重新认识黑猩猩，也重新认识人类", story: "她的长期野外观察显示黑猩猩会制作和使用工具。", contribution: "灵长类行为学", fact: "她在坦桑尼亚贡贝开展了数十年连续研究。" },
  { id: "vernadsky", month: 3, day: 12, name: "弗拉基米尔·维尔纳茨基", latinName: "Vladimir Vernadsky", years: "1863–1945", field: "地球科学", country: "乌克兰", color: "green", relation: "诞辰", tagline: "把生命看作塑造地球的力量", story: "他发展“生物圈”思想，强调生命与地球化学循环彼此交织。", contribution: "生物圈概念", fact: "他的思想影响了后来的地球系统科学。" },
  { id: "chandrasekhar", month: 10, day: 19, name: "苏布拉马尼扬·钱德拉塞卡", latinName: "S. Chandrasekhar", years: "1910–1995", field: "天文", country: "印度 / 美国", color: "blue", relation: "诞辰", tagline: "计算恒星坍缩前的极限", story: "他在年轻时推导出白矮星质量上限，为恒星演化和致密天体研究打下基础。", contribution: "钱德拉塞卡极限", fact: "他因恒星结构研究获得诺贝尔物理学奖。" },
  { id: "hubble", month: 11, day: 20, name: "埃德温·哈勃", latinName: "Edwin Hubble", years: "1889–1953", field: "天文", country: "美国", color: "gold", relation: "诞辰", tagline: "发现宇宙远比银河系辽阔", story: "他的观测表明许多“星云”是银河系外星系，并发现宇宙膨胀的证据。", contribution: "星系与宇宙膨胀观测", fact: "哈勃空间望远镜以他的名字命名。" },
  { id: "newton", month: 1, day: 4, name: "艾萨克·牛顿", latinName: "Isaac Newton", years: "1643–1727", field: "物理", country: "英国", color: "blue", relation: "诞辰", tagline: "把天上的运动写进同一组定律", story: "他用运动定律和万有引力定律连接地面与天体运动，建立经典力学的基本框架。", contribution: "经典力学与万有引力", fact: "《自然哲学的数学原理》发表于 1687 年。" },
  { id: "faraday", month: 9, day: 22, name: "迈克尔·法拉第", latinName: "Michael Faraday", years: "1791–1867", field: "物理", country: "英国", color: "gold", relation: "诞辰", tagline: "让看不见的电磁场变得可实验", story: "他通过电磁感应实验揭示电与磁之间的联系，为发电机和电动机奠定基础。", contribution: "电磁感应", fact: "法拉第还是一位出色的公众科学演讲者。" },
  { id: "maxwell", month: 6, day: 13, name: "詹姆斯·克拉克·麦克斯韦", latinName: "James Clerk Maxwell", years: "1831–1879", field: "物理", country: "英国", color: "violet", relation: "诞辰", tagline: "用方程把光、电与磁连成一体", story: "麦克斯韦方程组预言电磁波的传播，并揭示可见光只是电磁谱的一部分。", contribution: "电磁理论", fact: "他的理论后来成为无线通信和现代光学的基础。" },
  { id: "tesla", month: 7, day: 10, name: "尼古拉·特斯拉", latinName: "Nikola Tesla", years: "1856–1943", field: "物理", country: "塞尔维亚 / 美国", color: "coral", relation: "诞辰", tagline: "让交流电穿过城市与时代", story: "他推动交流电系统、感应电动机和无线通信实验发展，想象电力如何远距离流动。", contribution: "交流电系统", fact: "磁场强度单位特斯拉以他的名字命名。" },
  { id: "feynman", month: 5, day: 11, name: "理查德·费曼", latinName: "Richard Feynman", years: "1918–1988", field: "物理", country: "美国", color: "blue", relation: "诞辰", tagline: "把复杂的量子世界画成一条路径", story: "费曼图与路径积分为量子电动力学提供了直观又强大的计算语言。", contribution: "量子电动力学", fact: "他也以充满好奇心的物理教学和演讲闻名。" },
  { id: "pasteur", month: 12, day: 27, name: "路易·巴斯德", latinName: "Louis Pasteur", years: "1822–1895", field: "生命科学", country: "法国", color: "green", relation: "诞辰", tagline: "让微生物进入疾病与食品的故事", story: "他用实验支持微生物致病理论，发展巴氏消毒法和多种疫苗。", contribution: "微生物学与疫苗", fact: "巴氏消毒法最初用于防止葡萄酒和啤酒变质。" },
  { id: "euler", month: 4, day: 15, name: "莱昂哈德·欧拉", latinName: "Leonhard Euler", years: "1707–1783", field: "数学", country: "瑞士", color: "gold", relation: "诞辰", tagline: "让数学符号拥有清晰的秩序", story: "欧拉在分析、数论、图论和力学等领域留下大量基础成果，塑造了现代数学的表达方式。", contribution: "数学分析与图论", fact: "许多常用数学记号都在他的著作中得到推广。" },
  { id: "gauss", month: 4, day: 30, name: "卡尔·弗里德里希·高斯", latinName: "Carl Friedrich Gauss", years: "1777–1855", field: "数学", country: "德国", color: "violet", relation: "诞辰", tagline: "在数字、空间和误差中寻找规律", story: "高斯在数论、几何、天文学和测量学中建立了深远的方法与定理。", contribution: "数论与测量学", fact: "高斯分布和高斯定律都以他的名字命名。" },
  { id: "fleming", month: 8, day: 6, name: "亚历山大·弗莱明", latinName: "Alexander Fleming", years: "1881–1955", field: "医学", country: "英国", color: "green", relation: "诞辰", tagline: "从一块意外的霉菌中发现抗生素", story: "他观察到青霉菌抑制细菌生长，开启了青霉素及现代抗生素的故事。", contribution: "青霉素", fact: "青霉素的大规模应用还依赖后来团队的提纯与生产工作。" },
  { id: "mcclintock", month: 6, day: 16, name: "芭芭拉·麦克林托克", latinName: "Barbara McClintock", years: "1902–1992", field: "生命科学", country: "美国", color: "coral", relation: "诞辰", tagline: "发现基因并不总是安静地待在原地", story: "她在玉米研究中发现可移动遗传因子，改变了人们对基因组动态性的理解。", contribution: "转座子", fact: "她的成果多年后才被广泛认可，并获得诺贝尔奖。" },
  { id: "shannon", month: 4, day: 30, name: "克劳德·香农", latinName: "Claude Shannon", years: "1916–2001", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "把信息变成可以计算的东西", story: "信息论建立了衡量信息、噪声和通信容量的数学框架，影响了数字通信与压缩。", contribution: "信息论", fact: "他还用继电器电路研究布尔逻辑的机械实现。" },
  { id: "vonneumann", month: 12, day: 28, name: "约翰·冯·诺依曼", latinName: "John von Neumann", years: "1903–1957", field: "计算机", country: "匈牙利 / 美国", color: "blue", relation: "诞辰", tagline: "为存储程序计算机搭起骨架", story: "存储程序、算法和博弈论等思想，让计算机成为可以反复编程的通用机器。", contribution: "计算机体系结构", fact: "现代计算机常见的存储程序架构常被称为冯·诺依曼架构。" },
  { id: "bernerslee", month: 6, day: 8, name: "蒂姆·伯纳斯-李", latinName: "Tim Berners-Lee", years: "1955–", field: "计算机", country: "英国", color: "violet", relation: "诞辰", tagline: "让文档之间可以彼此链接", story: "他提出万维网的基本协议、地址和标记语言，让互联网成为开放的信息空间。", contribution: "万维网", fact: "他将万维网的核心技术公之于众，推动了开放网络的发展。" },
  { id: "leavitt", month: 7, day: 4, name: "亨丽埃塔·勒维特", latinName: "Henrietta Swan Leavitt", years: "1868–1921", field: "天文", country: "美国", color: "gold", relation: "诞辰", tagline: "用恒星的节奏丈量宇宙", story: "她发现造父变星的周期与亮度关系，为测量星系距离提供了关键标尺。", contribution: "造父变星关系", fact: "她的发现后来帮助天文学家确定银河系外星系的距离。" },
  { id: "rubin", month: 7, day: 23, name: "薇拉·鲁宾", latinName: "Vera Rubin", years: "1928–2016", field: "天文", country: "美国", color: "blue", relation: "诞辰", tagline: "从星系旋转看见不可见的质量", story: "她对星系旋转曲线的观测为暗物质存在提供了重要证据。", contribution: "暗物质观测证据", fact: "鲁宾天文台以她的名字命名。" },
  { id: "anning", month: 5, day: 21, name: "玛丽·安宁", latinName: "Mary Anning", years: "1799–1847", field: "地球科学", country: "英国", color: "green", relation: "诞辰", tagline: "在海岸线上读出远古生命", story: "她在英国莱姆里吉斯海岸发现并研究多种化石，推动了古生物学发展。", contribution: "化石与古生物学", fact: "她的发现改变了人们对史前海洋爬行动物的认识。" },
  { id: "wegener", month: 11, day: 1, name: "阿尔弗雷德·魏格纳", latinName: "Alfred Wegener", years: "1880–1930", field: "地球科学", country: "德国", color: "gold", relation: "诞辰", tagline: "让大陆开始缓慢地移动", story: "他提出大陆漂移假说，为后来板块构造理论的发展提供了重要线索。", contribution: "大陆漂移假说", fact: "早期假说一度受到质疑，直到海底扩张证据出现才获得支持。" },
  { id: "tuyouyou", month: 12, day: 30, name: "屠呦呦", latinName: "Tu Youyou", years: "1930–", field: "医学", country: "中国", color: "coral", relation: "诞辰", tagline: "从传统药方中寻找抗疟新线索", story: "她从青蒿中提取并改进青蒿素，为疟疾治疗带来重要药物。", contribution: "青蒿素", fact: "青蒿素相关研究获得诺贝尔生理学或医学奖。" },
  { id: "doudna", month: 2, day: 19, name: "詹妮弗·杜德纳", latinName: "Jennifer Doudna", years: "1964–", field: "生命科学", country: "美国", color: "violet", relation: "诞辰", tagline: "把基因编辑变成可以编程的工具", story: "她参与发展 CRISPR-Cas9 基因编辑技术，改变了生命科学实验的可能性。", contribution: "CRISPR 基因编辑", fact: "基因编辑的医学与伦理边界仍在持续讨论。" },
  { id: "wuchienShiung", month: 5, day: 31, name: "吴健雄", latinName: "Chien-Shiung Wu", years: "1912–1997", field: "物理", country: "中国 / 美国", color: "blue", relation: "诞辰", tagline: "用精密实验检验对称性的边界", story: "她以极高精度的实验检验宇称守恒问题，推动了粒子物理基本观念的修正。", contribution: "宇称不守恒实验", fact: "她被称为“物理学第一夫人”，并长期推动女性科学教育。" },
  { id: "johnson", month: 8, day: 26, name: "凯瑟琳·约翰逊", latinName: "Katherine Johnson", years: "1918–2020", field: "数学", country: "美国", color: "gold", relation: "诞辰", tagline: "用手算轨道把人送上太空", story: "她计算早期载人航天任务的轨道与再入路径，为太空飞行提供关键数学支持。", contribution: "航天轨道计算", fact: "她的工作后来通过 NASA 的公开档案与传记被更多人认识。" },
  { id: "kariko", month: 1, day: 17, name: "卡塔琳·考里科", latinName: "Katalin Karikó", years: "1955–", field: "医学", country: "匈牙利 / 美国", color: "coral", relation: "诞辰", tagline: "让信使 RNA 成为可用的医学平台", story: "她与合作者长期研究 RNA 修饰，为 mRNA 疫苗技术的发展奠定基础。", contribution: "mRNA 技术", fact: "她与德鲁·魏斯曼共同获得诺贝尔生理学或医学奖。" },
  { id: "hodgkin", month: 5, day: 12, name: "多萝西·霍奇金", latinName: "Dorothy Hodgkin", years: "1910–1994", field: "化学", country: "英国", color: "violet", relation: "诞辰", tagline: "用晶体中的光线看见分子结构", story: "她用 X 射线晶体学解析了青霉素、维生素 B12 等重要分子的结构。", contribution: "蛋白质与药物结构", fact: "她是 X 射线晶体学领域的重要开拓者。" },
  { id: "babbage", month: 12, day: 26, name: "查尔斯·巴贝奇", latinName: "Charles Babbage", years: "1791–1871", field: "计算机", country: "英国", color: "gold", relation: "诞辰", tagline: "在蒸汽时代想象可编程机器", story: "他设计差分机与分析机，提出了机械计算、存储和程序控制的早期构想。", contribution: "早期通用计算机", fact: "分析机的设计启发了后来对通用计算机的理解。" },
  { id: "ampere", month: 1, day: 20, name: "安德烈·玛丽·安培", latinName: "André-Marie Ampère", years: "1775–1836", field: "物理", country: "法国", color: "blue", relation: "诞辰", tagline: "为电流与磁场写下第一套语言", story: "安培研究载流导线之间的作用，建立电动力学早期理论。", contribution: "电动力学", fact: "电流单位安培以他的名字命名。" },
  { id: "leeuwenhoek", month: 10, day: 24, name: "安东尼·范·列文虎克", latinName: "Antonie van Leeuwenhoek", years: "1632–1723", field: "生命科学", country: "荷兰", color: "green", relation: "诞辰", tagline: "用自制镜片看见微小生命", story: "他改进显微镜并观察到细菌、原生动物等微小生命，开启微观世界的探索。", contribution: "显微观察", fact: "他制作的单透镜显微镜能达到当时极高的放大倍率。" },
  { id: "mendeleev", month: 2, day: 8, name: "德米特里·门捷列夫", latinName: "Dmitri Mendeleev", years: "1834–1907", field: "化学", country: "俄罗斯", color: "gold", relation: "诞辰", tagline: "给元素留下可以预测的空位", story: "他整理元素周期律，并大胆为尚未发现的元素预留位置。", contribution: "元素周期表", fact: "周期表中的周期性帮助化学家预测未知元素的性质。" },
  { id: "pauling", month: 2, day: 28, name: "莱纳斯·鲍林", latinName: "Linus Pauling", years: "1901–1994", field: "化学", country: "美国", color: "violet", relation: "诞辰", tagline: "从化学键看见分子的形状", story: "鲍林用量子力学解释化学键与分子结构，并推动分子生物学发展。", contribution: "化学键理论", fact: "他是少数两次独立获得诺贝尔奖的个人之一。" },
  { id: "gagarin", month: 3, day: 9, name: "尤里·加加林", latinName: "Yuri Gagarin", years: "1934–1968", field: "天文", country: "苏联", color: "blue", relation: "诞辰", tagline: "第一次从太空回望地球", story: "他乘东方一号完成首次载人地球轨道飞行，开启载人航天时代。", contribution: "载人航天", fact: "他的飞行历时约 108 分钟。" },
  { id: "priestley", month: 3, day: 13, name: "约瑟夫·普利斯特里", latinName: "Joseph Priestley", years: "1733–1804", field: "化学", country: "英国", color: "green", relation: "诞辰", tagline: "在气体实验中重新认识空气", story: "他分离并研究多种气体，为近代化学和燃烧理论的发展提供实验线索。", contribution: "气体化学", fact: "他的实验工作与氧气发现史密切相关。" },
  { id: "bunsen", month: 3, day: 30, name: "罗伯特·本生", latinName: "Robert Bunsen", years: "1811–1899", field: "化学", country: "德国", color: "coral", relation: "诞辰", tagline: "让火焰成为分析元素的光谱仪", story: "本生发展光谱分析方法，并与基尔霍夫合作发现多种元素。", contribution: "光谱分析", fact: "本生灯以他的名字命名，成为实验室常见工具。" },
  { id: "harvey", month: 4, day: 1, name: "威廉·哈维", latinName: "William Harvey", years: "1578–1657", field: "医学", country: "英国", color: "coral", relation: "诞辰", tagline: "用实验追踪血液循环的路径", story: "他通过解剖和实验论证心脏泵血及血液循环，为现代生理学奠定基础。", contribution: "血液循环理论", fact: "他的著作发表于 1628 年。" },
  { id: "merian", month: 4, day: 2, name: "玛丽亚·西比拉·梅里安", latinName: "Maria Sibylla Merian", years: "1647–1717", field: "生命科学", country: "德国 / 荷兰", color: "green", relation: "诞辰", tagline: "把昆虫的变化画成一生的故事", story: "她观察并记录昆虫的变态过程，用精细图谱连接自然史与艺术。", contribution: "昆虫学与自然史", fact: "她曾远赴苏里南开展热带昆虫观察。" },
  { id: "watson", month: 4, day: 6, name: "詹姆斯·沃森", latinName: "James Watson", years: "1928–", field: "生命科学", country: "美国", color: "violet", relation: "诞辰", tagline: "从双螺旋看见遗传信息的形状", story: "他与合作者提出 DNA 双螺旋结构模型，推动分子生物学成为一门新学科。", contribution: "DNA 双螺旋模型", fact: "DNA 结构研究汇集了多位研究者的实验与图像证据。" },
  { id: "planck", month: 4, day: 23, name: "马克斯·普朗克", latinName: "Max Planck", years: "1858–1947", field: "物理", country: "德国", color: "blue", relation: "诞辰", tagline: "让能量以一份一份的方式出现", story: "他提出能量量子化假设，为量子物理的诞生打开入口。", contribution: "量子假说", fact: "普朗克常数是量子理论的基本常数。" },
  { id: "pierrecerie", month: 5, day: 15, name: "皮埃尔·居里", latinName: "Pierre Curie", years: "1859–1906", field: "物理", country: "法国", color: "gold", relation: "诞辰", tagline: "在晶体与磁性之间寻找秩序", story: "他研究压电效应、磁性与放射性，并与玛丽·居里共同推进放射性研究。", contribution: "压电效应与放射性", fact: "压电效应后来成为超声和精密传感技术的基础。" },
  { id: "apgar", month: 6, day: 7, name: "弗吉尼亚·阿普加", latinName: "Virginia Apgar", years: "1909–1974", field: "医学", country: "美国", color: "coral", relation: "诞辰", tagline: "用五个指标守护新生儿的第一分钟", story: "她建立阿普加评分，帮助医护人员快速判断新生儿的生命状态。", contribution: "新生儿评分", fact: "阿普加评分至今仍是产科和新生儿护理的重要工具。" },
  { id: "cousteau", month: 6, day: 11, name: "雅克·库斯托", latinName: "Jacques Cousteau", years: "1910–1997", field: "地球科学", country: "法国", color: "blue", relation: "诞辰", tagline: "让更多人看见海洋深处", story: "他改进水下呼吸设备并通过纪录片传播海洋生态与保护理念。", contribution: "海洋探索与传播", fact: "他的水下影像让海洋科学进入大众文化。" },
  { id: "crick", month: 6, day: 8, name: "弗朗西斯·克里克", latinName: "Francis Crick", years: "1916–2004", field: "生命科学", country: "英国", color: "violet", relation: "诞辰", tagline: "从分子结构追问遗传信息如何传递", story: "他参与提出 DNA 双螺旋结构，并阐释遗传信息传递的中心法则。", contribution: "分子生物学中心法则", fact: "中心法则描述了遗传信息在分子系统中的基本流向。" },
  { id: "pascal", month: 6, day: 19, name: "布莱兹·帕斯卡", latinName: "Blaise Pascal", years: "1623–1662", field: "数学", country: "法国", color: "gold", relation: "诞辰", tagline: "在概率、压力与计算之间搭桥", story: "帕斯卡研究概率、流体静力学，并设计早期机械计算器。", contribution: "概率论与流体静力学", fact: "压力单位帕斯卡以他的名字命名。" },
  { id: "armstrong", month: 8, day: 5, name: "尼尔·阿姆斯特朗", latinName: "Neil Armstrong", years: "1930–2012", field: "天文", country: "美国", color: "gold", relation: "诞辰", tagline: "把人类的脚印留在另一个天体", story: "他作为阿波罗十一号指令长完成首次载人登月，拓展了人类对月球的探索。", contribution: "载人登月", fact: "阿波罗十一号于 1969 年登上月球。" },
  { id: "bohr", month: 10, day: 7, name: "尼尔斯·玻尔", latinName: "Niels Bohr", years: "1885–1962", field: "物理", country: "丹麦", color: "violet", relation: "诞辰", tagline: "让原子拥有离散的能级", story: "玻尔模型与互补原理帮助人们理解原子结构和量子现象。", contribution: "原子结构与量子理论", fact: "哥本哈根学派围绕他的研究所形成。" },
  { id: "salk", month: 10, day: 28, name: "乔纳斯·索尔克", latinName: "Jonas Salk", years: "1914–1995", field: "医学", country: "美国", color: "green", relation: "诞辰", tagline: "让疫苗改变一种疾病的命运", story: "他领导团队研发脊髓灰质炎灭活疫苗，为公共卫生带来重要突破。", contribution: "脊髓灰质炎疫苗", fact: "疫苗试验曾覆盖大规模儿童群体。" },
  { id: "chern", month: 10, day: 28, name: "陈省身", latinName: "Shiing-Shen Chern", years: "1911–2004", field: "数学", country: "中国 / 美国", color: "coral", relation: "诞辰", tagline: "用几何语言理解空间的整体形状", story: "陈省身在微分几何和拓扑学中建立了深远理论，影响现代数学与物理。", contribution: "微分几何与拓扑", fact: "陈类是现代几何拓扑中的重要不变量。" },
  { id: "sagan", month: 11, day: 9, name: "卡尔·萨根", latinName: "Carl Sagan", years: "1934–1996", field: "天文", country: "美国", color: "blue", relation: "诞辰", tagline: "把宇宙的尺度带进每个人的客厅", story: "他研究行星科学并通过写作与电视节目传播天文学和科学思维。", contribution: "行星科学与科普", fact: "他参与设计旅行者号携带的金唱片。" },
  { id: "meitner", month: 11, day: 7, name: "莉泽·迈特纳", latinName: "Lise Meitner", years: "1878–1968", field: "物理", country: "奥地利 / 瑞典", color: "violet", relation: "诞辰", tagline: "从原子核裂变理解能量的释放", story: "她与合作者解释了核裂变现象，为核物理发展提供关键理论。", contribution: "核裂变理论解释", fact: "元素 109 迈特纳ium 以她的名字命名。" },
  { id: "bath", month: 11, day: 4, name: "帕特里夏·巴思", latinName: "Patricia Bath", years: "1942–2019", field: "医学", country: "美国", color: "coral", relation: "诞辰", tagline: "让眼科手术更精准地恢复视力", story: "她发明激光白内障手术设备，并推动社区眼科保健与视力平等。", contribution: "激光眼科手术", fact: "她是美国第一位获得医学发明专利的非裔女性医生。" },
  { id: "ramanujan", month: 12, day: 22, name: "斯里尼瓦瑟·拉马努金", latinName: "Srinivasa Ramanujan", years: "1887–1920", field: "数学", country: "印度", color: "gold", relation: "诞辰", tagline: "从直觉中写出数的深层规律", story: "拉马努金在数论、级数与分拆函数方面留下大量富有洞察力的公式。", contribution: "数论与无穷级数", fact: "许多手稿中的公式在后来几十年里持续得到证明与推广。" },
  { id: "michelson", month: 12, day: 19, name: "阿尔伯特·迈克耳孙", latinName: "Albert A. Michelson", years: "1852–1931", field: "物理", country: "美国", color: "blue", relation: "诞辰", tagline: "用光的干涉测量世界的精细差异", story: "他发展高精度光学测量并参与迈克耳孙—莫雷实验，为现代物理提供关键证据。", contribution: "光速与干涉测量", fact: "他是第一位获得诺贝尔物理学奖的美国科学家。" },
  { id: "hinton", month: 12, day: 6, name: "杰弗里·辛顿", latinName: "Geoffrey Hinton", years: "1947–", field: "计算机", country: "英国 / 加拿大", color: "violet", relation: "诞辰", tagline: "让神经网络学会从数据中提取层次", story: "他推动反向传播、深度学习与神经网络研究，改变了机器学习的发展路径。", contribution: "深度学习", fact: "深度神经网络已广泛用于视觉、语言与科学计算。" },
  { id: "watt", month: 1, day: 19, name: "詹姆斯·瓦特", latinName: "James Watt", years: "1736–1819", field: "物理", country: "英国", color: "gold", relation: "诞辰", tagline: "让蒸汽机真正走进工业时代", story: "他改进蒸汽机的冷凝与效率，推动热能机械从实验走向大规模应用。", contribution: "蒸汽机改良", fact: "功率单位瓦特以他的名字命名。" },
  { id: "boyle", month: 1, day: 25, name: "罗伯特·波义耳", latinName: "Robert Boyle", years: "1627–1691", field: "化学", country: "爱尔兰 / 英国", color: "violet", relation: "诞辰", tagline: "让化学实验开始遵循可重复的规则", story: "波义耳研究气体压力与体积关系，并推动实验方法成为化学知识的核心。", contribution: "波义耳定律", fact: "他也参与创立英国皇家学会。" },
  { id: "hertz", month: 2, day: 22, name: "海因里希·赫兹", latinName: "Heinrich Hertz", years: "1857–1894", field: "物理", country: "德国", color: "blue", relation: "诞辰", tagline: "用实验捕捉电磁波的存在", story: "赫兹在实验室产生并检测电磁波，为麦克斯韦理论提供了直接证据。", contribution: "电磁波实验", fact: "频率单位赫兹以他的名字命名。" },
  { id: "descartes", month: 3, day: 31, name: "勒内·笛卡尔", latinName: "René Descartes", years: "1596–1650", field: "数学", country: "法国", color: "coral", relation: "诞辰", tagline: "用坐标把几何图形写成方程", story: "笛卡尔将代数与几何连接起来，坐标方法改变了数学与自然科学的表达方式。", contribution: "解析几何", fact: "笛卡尔坐标系至今仍是数学和物理的基础语言。" },
  { id: "ohm", month: 3, day: 16, name: "乔治·欧姆", latinName: "Georg Ohm", years: "1789–1854", field: "物理", country: "德国", color: "green", relation: "诞辰", tagline: "把电流、电压与电阻写进一条关系", story: "欧姆通过实验建立电路中电流、电压和电阻之间的定量关系。", contribution: "欧姆定律", fact: "电阻单位欧姆以他的名字命名。" },
  { id: "vonbraun", month: 3, day: 23, name: "沃纳·冯·布劳恩", latinName: "Wernher von Braun", years: "1912–1977", field: "天文", country: "德国 / 美国", color: "gold", relation: "诞辰", tagline: "把火箭工程推向载人航天", story: "他参与大型运载火箭设计与航天工程组织，推动人类探索月球。", contribution: "运载火箭工程", fact: "土星五号火箭将阿波罗宇航员送往月球。" },
  { id: "morse", month: 4, day: 27, name: "塞缪尔·莫尔斯", latinName: "Samuel Morse", years: "1791–1872", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "用点与划让消息跨越远方", story: "他发展电报系统与莫尔斯电码，改变了远距离通信的速度。", contribution: "电报与编码", fact: "莫尔斯电码把字母转换为简短的信号序列。" },
  { id: "jenner", month: 5, day: 17, name: "爱德华·詹纳", latinName: "Edward Jenner", years: "1749–1823", field: "医学", country: "英国", color: "green", relation: "诞辰", tagline: "用一次接种改变传染病的命运", story: "詹纳观察牛痘对天花的保护作用，建立早期疫苗接种方法。", contribution: "天花疫苗", fact: "天花后来成为人类通过公共卫生消灭的首种疾病。" },
  { id: "land", month: 5, day: 7, name: "埃德温·兰德", latinName: "Edwin H. Land", years: "1909–1991", field: "物理", country: "美国", color: "violet", relation: "诞辰", tagline: "让光线在几分钟内变成一张照片", story: "他研究偏振材料并发明即时成像技术，让摄影从等待冲洗变成即时反馈。", contribution: "偏振材料与即时成像", fact: "偏振片也广泛用于光学仪器和显示技术。" },
  { id: "strickland", month: 5, day: 27, name: "唐娜·斯特里克兰", latinName: "Donna Strickland", years: "1959–", field: "物理", country: "加拿大", color: "coral", relation: "诞辰", tagline: "让激光脉冲变得更短、更强", story: "她与合作者发展啁啾脉冲放大技术，推动超快激光在医学和工业中的应用。", contribution: "超快激光", fact: "她因这项工作获得诺贝尔物理学奖。" },
  { id: "hamilton", month: 8, day: 17, name: "玛格丽特·汉密尔顿", latinName: "Margaret Hamilton", years: "1936–", field: "计算机", country: "美国", color: "blue", relation: "诞辰", tagline: "让登月软件在关键时刻保持可靠", story: "她领导阿波罗导航软件团队，推动软件工程成为严谨的工程学科。", contribution: "航天软件工程", fact: "她的团队为系统设计了优先级调度和故障处理机制。" },
  { id: "dirac", month: 8, day: 8, name: "保罗·狄拉克", latinName: "Paul Dirac", years: "1902–1984", field: "物理", country: "英国", color: "violet", relation: "诞辰", tagline: "用一个方程预言反物质", story: "狄拉克方程把量子力学与狭义相对论结合，并预言反粒子的存在。", contribution: "狄拉克方程", fact: "他的数学形式至今仍是量子场论的重要基础。" },
  { id: "arnold", month: 7, day: 25, name: "弗朗西斯·阿诺德", latinName: "Frances Arnold", years: "1956–", field: "化学", country: "美国", color: "green", relation: "诞辰", tagline: "让进化在实验室里改造酶", story: "她发展定向进化方法，利用变异与筛选设计更适合人类需要的酶。", contribution: "酶的定向进化", fact: "定向进化已用于药物、材料和可持续化学。" },
  { id: "ritchie", month: 9, day: 9, name: "丹尼斯·里奇", latinName: "Dennis Ritchie", years: "1941–2011", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "用简洁的语言搭起软件世界", story: "他设计 C 语言并参与 Unix 系统开发，深刻影响现代操作系统与软件工程。", contribution: "C 语言与 Unix", fact: "C 语言至今仍是系统软件和嵌入式开发的重要工具。" },
  { id: "vaughan", month: 9, day: 20, name: "多萝西·沃恩", latinName: "Dorothy Vaughan", years: "1910–2008", field: "数学", country: "美国", color: "gold", relation: "诞辰", tagline: "从人工计算走向编程时代", story: "她领导 NASA 的西部地区计算组，并自学 FORTRAN 带领团队转向电子计算。", contribution: "航天计算与编程", fact: "她的团队参与了早期航天和气象计算任务。" },
  { id: "alfred-nobel", month: 10, day: 21, name: "阿尔弗雷德·诺贝尔", latinName: "Alfred Nobel", years: "1833–1896", field: "化学", country: "瑞典", color: "gold", relation: "诞辰", tagline: "让科学成就拥有持续被纪念的制度", story: "他研究炸药与工业材料，并在遗嘱中设立诺贝尔奖，支持推动人类进步的工作。", contribution: "炸药化学与科学奖励", fact: "诺贝尔奖自 1901 年起颁发。" },
  { id: "boole", month: 11, day: 2, name: "乔治·布尔", latinName: "George Boole", years: "1815–1864", field: "数学", country: "英国", color: "violet", relation: "诞辰", tagline: "把逻辑推理写成可以计算的代数", story: "布尔代数把命题逻辑形式化，后来成为数字电路和计算机逻辑的基础。", contribution: "布尔代数", fact: "现代程序中的真假判断仍能追溯到布尔逻辑。" },
  { id: "kepler", month: 12, day: 27, name: "约翰内斯·开普勒", latinName: "Johannes Kepler", years: "1571–1630", field: "天文", country: "德国", color: "blue", relation: "诞辰", tagline: "从行星轨道中读出宇宙的几何", story: "开普勒从观测数据中总结行星运动三定律，揭示行星轨道并非完美圆形。", contribution: "行星运动定律", fact: "他的定律为牛顿万有引力理论提供了重要线索。" },
  { id: "brahe", month: 12, day: 14, name: "第谷·布拉赫", latinName: "Tycho Brahe", years: "1546–1601", field: "天文", country: "丹麦", color: "gold", relation: "诞辰", tagline: "用肉眼观测积累一座星空档案馆", story: "他在望远镜出现前进行高精度天文观测，为开普勒建立行星运动定律提供数据。", contribution: "精密天文观测", fact: "他的观测记录包含超新星和彗星等重要天象。" },
  { id: "halley", month: 10, day: 8, name: "埃德蒙·哈雷", latinName: "Edmond Halley", years: "1656–1742", field: "天文", country: "英国", color: "blue", relation: "诞辰", tagline: "让彗星的回归成为可以预测的事件", story: "哈雷利用历史观测和牛顿力学预测一颗彗星将再次出现，展示科学如何连接时间与轨道。", contribution: "彗星轨道预测", fact: "哈雷彗星约每 76 年回归一次。" },
  { id: "germain", month: 1, day: 13, name: "索菲·热尔曼", latinName: "Sophie Germain", years: "1776–1831", field: "数学", country: "法国", color: "violet", relation: "诞辰", tagline: "在看不见的阻力中坚持写下数学", story: "热尔曼研究数论和弹性理论，在女性难以进入学术机构的时代留下重要工作。", contribution: "数论与弹性理论", fact: "她曾用化名与数学家通信以绕开时代限制。" },
  { id: "engelbart", month: 1, day: 30, name: "道格拉斯·恩格尔巴特", latinName: "Douglas Engelbart", years: "1925–2013", field: "计算机", country: "美国", color: "coral", relation: "诞辰", tagline: "让人机交互从命令行走向可操作的空间", story: "恩格尔巴特展示了鼠标、超文本和协同编辑等概念，影响了个人计算的未来形态。", contribution: "人机交互", fact: "1968 年的演示后来被称为“所有演示之母”。" },
  { id: "segre", month: 2, day: 1, name: "埃米利奥·塞格雷", latinName: "Emilio Segrè", years: "1905–1989", field: "物理", country: "意大利 / 美国", color: "blue", relation: "诞辰", tagline: "在粒子轨迹中寻找反物质的证据", story: "塞格雷参与发现锝元素，并因反质子的发现获得诺贝尔物理学奖。", contribution: "反质子发现", fact: "锝是第一个人工制得的元素。" },
  { id: "blackwell", month: 2, day: 3, name: "伊丽莎白·布莱克威尔", latinName: "Elizabeth Blackwell", years: "1821–1910", field: "医学", country: "英国 / 美国", color: "green", relation: "诞辰", tagline: "把女性进入医学职业变成现实", story: "布莱克威尔成为美国第一位获得医学学位的女性，并推动女性医学教育。", contribution: "医学教育", fact: "她创办的机构为女性医生提供训练和实践机会。" },
  { id: "shockley", month: 2, day: 13, name: "威廉·肖克利", latinName: "William Shockley", years: "1910–1989", field: "物理", country: "英国 / 美国", color: "gold", relation: "诞辰", tagline: "让固体物理变成电子时代的开关", story: "肖克利参与晶体管研究，使半导体技术成为现代电子工业的基础。", contribution: "晶体管物理", fact: "晶体管改变了计算机、通信和消费电子的尺度。" },
  { id: "mercator", month: 3, day: 5, name: "杰拉杜斯·墨卡托", latinName: "Gerardus Mercator", years: "1512–1594", field: "地球科学", country: "佛兰德", color: "gold", relation: "诞辰", tagline: "把球面世界摊开成航海者能读懂的地图", story: "墨卡托投影让等角航线能以直线呈现，深刻影响了航海与地图制作。", contribution: "地图投影", fact: "“atlas”作为地图集概念与他的作品密切相关。" },
  { id: "fitch", month: 3, day: 10, name: "瓦尔·菲奇", latinName: "Val Logsdon Fitch", years: "1923–2015", field: "物理", country: "美国", color: "blue", relation: "诞辰", tagline: "在粒子的微小偏差中看见对称性破缺", story: "菲奇与克罗宁发现中性 K 介子中的 CP 破坏现象，改变了粒子物理对对称性的理解。", contribution: "CP 破坏发现", fact: "CP 破坏与宇宙中物质和反物质不对称问题有关。" },
  { id: "behring", month: 3, day: 15, name: "埃米尔·冯·贝林", latinName: "Emil von Behring", years: "1854–1917", field: "医学", country: "德国", color: "green", relation: "诞辰", tagline: "让血清疗法成为抵抗传染病的武器", story: "贝林发展白喉抗毒素疗法，推动免疫学和传染病治疗进入新阶段。", contribution: "血清疗法", fact: "他获得首届诺贝尔生理学或医学奖。" },
  { id: "fourier", month: 3, day: 21, name: "约瑟夫·傅里叶", latinName: "Joseph Fourier", years: "1768–1830", field: "数学", country: "法国", color: "coral", relation: "诞辰", tagline: "把复杂波形拆成可理解的频率", story: "傅里叶研究热传导，并提出把函数分解为三角级数的方法，影响了现代分析和信号处理。", contribution: "傅里叶分析", fact: "从音频压缩到医学成像，都能看到傅里叶方法的影子。" },
  { id: "david-blackwell", month: 4, day: 24, name: "戴维·布莱克韦尔", latinName: "David Blackwell", years: "1919–2010", field: "数学", country: "美国", color: "violet", relation: "诞辰", tagline: "在概率、统计与决策之间建立清晰道路", story: "布莱克韦尔在统计、博弈论和动态规划方面贡献深远，是重要的数学家和教育者。", contribution: "统计决策理论", fact: "他是首位当选美国国家科学院院士的非裔美国人之一。" },
  { id: "penzias", month: 4, day: 26, name: "阿诺·彭齐亚斯", latinName: "Arno Penzias", years: "1933–2024", field: "天文", country: "德国 / 美国", color: "blue", relation: "诞辰", tagline: "从天线噪声中听见宇宙早期的余温", story: "彭齐亚斯与威尔逊发现宇宙微波背景辐射，为大爆炸宇宙学提供关键证据。", contribution: "宇宙微波背景", fact: "他们最初以为噪声来自仪器和环境。" },
  { id: "oort", month: 4, day: 28, name: "扬·奥尔特", latinName: "Jan Oort", years: "1900–1992", field: "天文", country: "荷兰", color: "gold", relation: "诞辰", tagline: "用银河旋转理解恒星的家园", story: "奥尔特研究银河系结构和旋转，并提出遥远彗星云的概念。", contribution: "银河系动力学", fact: "奥尔特云以他的名字命名。" },
  { id: "bose", month: 5, day: 2, name: "萨特延德拉·玻色", latinName: "Satyendra Nath Bose", years: "1894–1974", field: "物理", country: "印度", color: "blue", relation: "诞辰", tagline: "让量子粒子拥有新的统计语言", story: "玻色提出光子的统计方法，启发爱因斯坦发展玻色-爱因斯坦统计。", contribution: "玻色-爱因斯坦统计", fact: "“玻色子”以他的名字命名。" },
  { id: "huxley", month: 5, day: 4, name: "托马斯·亨利·赫胥黎", latinName: "Thomas Henry Huxley", years: "1825–1895", field: "生命科学", country: "英国", color: "green", relation: "诞辰", tagline: "把进化论带进公共辩论的现场", story: "赫胥黎研究比较解剖学，也积极为达尔文进化论进行公开辩护和科学传播。", contribution: "进化论传播", fact: "他被称为“达尔文的斗犬”。" },
  { id: "higgs", month: 5, day: 29, name: "彼得·希格斯", latinName: "Peter Higgs", years: "1929–2024", field: "物理", country: "英国", color: "violet", relation: "诞辰", tagline: "让质量的来源成为可寻找的粒子", story: "希格斯机制解释基本粒子如何获得质量，希格斯玻色子的发现验证了标准模型的重要部分。", contribution: "希格斯机制", fact: "大型强子对撞机在 2012 年宣布发现类似希格斯玻色子的粒子。" },
  { id: "charles-drew", month: 6, day: 3, name: "查尔斯·德鲁", latinName: "Charles R. Drew", years: "1904–1950", field: "医学", country: "美国", color: "coral", relation: "诞辰", tagline: "让血液保存和输血体系更加可靠", story: "德鲁改进血浆保存与血库组织方式，在战时和公共医疗中发挥重要作用。", contribution: "血库与输血医学", fact: "他的工作帮助建立现代血液储存和分配体系。" },
  { id: "couch-adams", month: 6, day: 5, name: "约翰·柯西·亚当斯", latinName: "John Couch Adams", years: "1819–1892", field: "天文", country: "英国", color: "gold", relation: "诞辰", tagline: "用计算追踪尚未被看见的行星", story: "亚当斯通过天王星轨道异常推算海王星位置，是数学天文学的经典案例之一。", contribution: "海王星轨道预测", fact: "勒威耶也独立完成了类似计算。" },
  { id: "kelvin", month: 6, day: 26, name: "威廉·汤姆森", latinName: "William Thomson, Lord Kelvin", years: "1824–1907", field: "物理", country: "英国", color: "blue", relation: "诞辰", tagline: "把温度和能量放进更精确的尺度", story: "开尔文在热力学、电磁学和海底电缆工程中都有重要贡献，推动精密测量成为现代科学语言。", contribution: "热力学与绝对温标", fact: "开尔文温标以他的封号命名。" },
  { id: "wheeler", month: 7, day: 9, name: "约翰·惠勒", latinName: "John Archibald Wheeler", years: "1911–2008", field: "物理", country: "美国", color: "violet", relation: "诞辰", tagline: "给黑洞这个名字，也给宇宙更多问题", story: "惠勒研究广义相对论、量子理论和核物理，是 20 世纪理论物理的重要教师与思想者。", contribution: "黑洞与相对论研究", fact: "“black hole”一词因他的推广而广泛流行。" },
  { id: "maria-mitchell", month: 8, day: 1, name: "玛丽亚·米切尔", latinName: "Maria Mitchell", years: "1818–1889", field: "天文", country: "美国", color: "green", relation: "诞辰", tagline: "在望远镜里为女性科学家打开天空", story: "米切尔发现彗星，并成为美国早期重要女性天文学家和科学教育者。", contribution: "彗星发现与天文教育", fact: "她是美国文理科学院首批女性成员之一。" },
  { id: "kekule", month: 9, day: 7, name: "弗里德里希·凯库勒", latinName: "August Kekulé", years: "1829–1896", field: "化学", country: "德国", color: "green", relation: "诞辰", tagline: "把有机化学带入环状结构的想象", story: "凯库勒提出苯环结构，让分子结构理论有了一个决定性的转折。", contribution: "苯环结构", fact: "他关于苯环的故事常被视为化学史上的经典瞬间。" },
  { id: "fermi", month: 9, day: 29, name: "恩里科·费米", latinName: "Enrico Fermi", years: "1901–1954", field: "物理", country: "意大利 / 美国", color: "blue", relation: "诞辰", tagline: "把原子核变成可计算的世界", story: "费米在核物理、粒子统计和反应堆设计中都留下了决定性贡献。", contribution: "核物理与反应堆", fact: "芝加哥一号堆实现了人类首次受控核链式反应。" },
  { id: "goddard", month: 10, day: 5, name: "罗伯特·戈达德", latinName: "Robert H. Goddard", years: "1882–1945", field: "物理", country: "美国", color: "coral", relation: "诞辰", tagline: "让火箭从想象变成工程", story: "戈达德推动液体燃料火箭研究，为现代航天技术奠定工程基础。", contribution: "液体火箭", fact: "他在火箭推进方面的许多理念后来都被航天工业采用。" },
  { id: "bohr", month: 10, day: 7, name: "尼尔斯·玻尔", latinName: "Niels Bohr", years: "1885–1962", field: "物理", country: "丹麦", color: "blue", relation: "诞辰", tagline: "为原子结构写下量子规则", story: "玻尔模型用量子化轨道解释原子光谱，是现代量子论的重要起点。", contribution: "玻尔原子模型", fact: "哥本哈根学派影响了整整一代量子物理学家。" },
  { id: "chadwick", month: 10, day: 20, name: "詹姆斯·查德威克", latinName: "James Chadwick", years: "1891–1974", field: "物理", country: "英国", color: "gold", relation: "诞辰", tagline: "为原子核补上中子这一块", story: "查德威克发现中子，解释了原子核中电荷与质量的关系。", contribution: "中子发现", fact: "中子的发现开启了大量核物理与核工程研究。" },
  { id: "pauling", month: 2, day: 28, name: "莱纳斯·鲍林", latinName: "Linus Pauling", years: "1901–1994", field: "化学", country: "美国", color: "violet", relation: "诞辰", tagline: "把化学键变成一门精确的语言", story: "鲍林用量子化学解释化学键与分子结构，深刻影响现代化学。", contribution: "化学键理论", fact: "他是少数两次独享诺贝尔奖的人之一。" },
  { id: "levi-montalcini", month: 4, day: 22, name: "丽塔·列维-蒙塔尔奇尼", latinName: "Rita Levi-Montalcini", years: "1909–2012", field: "生命科学", country: "意大利", color: "green", relation: "诞辰", tagline: "在神经系统里找到生长的信号", story: "她发现神经生长因子，推动神经科学与发育生物学的研究。", contribution: "神经生长因子", fact: "她晚年仍活跃于科学与公共事务。" },
  { id: "yalow", month: 7, day: 19, name: "罗莎琳·亚洛", latinName: "Rosalyn Yalow", years: "1921–2011", field: "医学", country: "美国", color: "coral", relation: "诞辰", tagline: "让微量激素也能被准确测量", story: "亚洛发展放射免疫测定法，使临床与基础医学都能测量极低浓度分子。", contribution: "放射免疫测定", fact: "这项方法改变了激素、病毒与药物检测的精度。" },
  { id: "heisenberg", month: 12, day: 5, name: "维尔纳·海森堡", latinName: "Werner Heisenberg", years: "1901–1976", field: "物理", country: "德国", color: "violet", relation: "诞辰", tagline: "给量子世界写下不确定性", story: "海森堡推动矩阵力学并提出不确定性原理，重塑了量子理论。", contribution: "矩阵力学与不确定性原理", fact: "量子测量的极限是现代物理的核心主题之一。" },
  { id: "sagan", month: 11, day: 9, name: "卡尔·萨根", latinName: "Carl Sagan", years: "1934–1996", field: "天文", country: "美国", color: "gold", relation: "诞辰", tagline: "把宇宙讲给所有人听", story: "萨根研究行星科学，也让公众重新爱上了天文学与宇宙探索。", contribution: "行星科学与科普", fact: "他主持的《宇宙》影响了几代科学爱好者。" },
];

const fields: Array<Field | "全部"> = ["全部", "物理", "化学", "生命科学", "数学", "计算机", "天文", "医学", "地球科学"];
const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"];
const weekdayNames = ["日", "一", "二", "三", "四", "五", "六"];

function formatDate(month: number, day: number) {
  return `${month} 月 ${day} 日`;
}

export default function Home() {
  const [activeField, setActiveField] = useState<Field | "全部">("全部");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("einstein");
  const [calendarMonth, setCalendarMonth] = useState(7);

  const selected = scientists.find((scientist) => scientist.id === selectedId) ?? scientists[0];
  const selectedQuote = quotes[selected.id as keyof typeof quotes];
  const filtered = useMemo(() => scientists.filter((scientist) => {
    const inField = activeField === "全部" || scientist.field === activeField;
    const needle = query.trim().toLowerCase();
    const inSearch = !needle || [scientist.name, scientist.latinName, scientist.field, scientist.country, scientist.contribution].join(" ").toLowerCase().includes(needle);
    return inField && inSearch;
  }), [activeField, query]);

  const monthDays = new Date(2026, calendarMonth, 0).getDate();
  const firstWeekday = new Date(2026, calendarMonth - 1, 1).getDay();
  const monthEntries = scientists.filter((scientist) => scientist.month === calendarMonth);
  const coveredDays = new Set(scientists.map((scientist) => `${scientist.month}-${scientist.day}`)).size;
  const coveragePercent = Math.min(100, (coveredDays / 365) * 100);

  function selectScientist(scientist: Scientist) {
    setSelectedId(scientist.id);
    setCalendarMonth(scientist.month);
    document.getElementById("today")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main>
      <nav className="site-nav" aria-label="主导航">
        <a className="brand" href="#top" aria-label="科学家日历首页"><span className="brand-mark">∴</span> 科学家日历</a>
        <div className="nav-links"><a href="#calendar">日历</a><a href="#explore">探索</a><a href="#about">关于</a></div>
        <a className="nav-action" href="#explore">开始探索 <span>↗</span></a>
      </nav>

      <section className="hero" id="top" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">THE DAILY SCIENCE NOTEBOOK · 2026</p>
          <h1 id="hero-title">每天，<br /><em>遇见一个</em><br />改变世界的念头。</h1>
          <p className="hero-text">一份写给好奇心的科学日历。从一位科学家、一项发现，走进人类理解世界的方式。</p>
          <div className="hero-actions"><a className="button-primary" href="#today">阅读今日人物 <span>↓</span></a><a className="button-secondary" href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`} download>获取 A4 打印版 <span>↓</span></a><a className="text-link" href="#calendar">查看月历 <span>→</span></a></div>
        </div>
        <div className="orbit-art" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" />
          <div className="star star-a" /> <div className="star star-b" /> <div className="star star-c" />
          <div className="hero-disc"><span>365</span><small>种好奇</small></div>
          <p className="art-caption">每一个答案<br />都从一个问题开始</p>
        </div>
      </section>

      <section className="overview-strip" aria-label="日历内容概览">
        <div><strong>{scientists.length}</strong><span>位人物档案</span></div>
        <div><strong>{fields.length - 1}</strong><span>个科学领域</span></div>
        <div><strong>{coveredDays}</strong><span>个已覆盖日期</span></div>
        <p className="coverage-note">全年覆盖进度 <strong>{coveredDays} / 365</strong><span className="coverage-bar"><i style={{ width: `${coveragePercent}%` }} /></span></p>
      </section>

      <section className="today-section" id="today" aria-labelledby="today-title">
        <header className="section-heading"><div><p className="eyebrow">TODAY&apos;S NOTE · {formatDate(selected.month, selected.day)}</p><h2 id="today-title">今日人物</h2></div><p className="section-aside">第 {String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")} 页 / 365</p></header>
        <article className={`feature-card tone-${selected.color}`}>
          <div className="portrait-panel"><span className="portrait-number">{String(selected.month).padStart(2, "0")}.{String(selected.day).padStart(2, "0")}</span>{selected.id === "einstein" ? <img className="portrait-illustration" src="art/einstein-archive.webp" alt="阿尔伯特·爱因斯坦的复古科学插画肖像" /> : <div className={`portrait-abstract tone-${selected.color}`} aria-hidden="true"><i /><b>{selected.name.slice(0, 1)}</b><em>{selected.latinName}</em></div>}<span className="portrait-field">{selected.field}</span></div>
          <div className="feature-copy"><p className="feature-relation">{selected.relation} · {selected.years}</p><h3>{selected.name}</h3><p className="latin-name">{selected.latinName} · {selected.country}</p><p className="feature-tagline">“{selected.tagline}”</p>{selectedQuote && <blockquote className="quote-block"><span>今日引语</span><p>“{selectedQuote.text}”</p><cite>— {selectedQuote.source}</cite></blockquote>}<p className="feature-story">{selected.story}</p><div className="feature-meta"><div><span>核心贡献</span><strong>{selected.contribution}</strong></div><div><span>你知道吗</span><strong>{selected.fact}</strong></div></div><button className="detail-button" type="button" onClick={() => document.getElementById("explore")?.scrollIntoView({ behavior: "smooth" })}>在档案库中继续探索 <span>→</span></button></div>
          <div className="feature-index" aria-hidden="true"><span>SCIENCE</span><span>NOTE</span><b>{selected.id.slice(0, 3).toUpperCase()}</b></div>
        </article>
      </section>

      <section className="calendar-section" id="calendar" aria-labelledby="calendar-title">
        <header className="section-heading"><div><p className="eyebrow">SCIENCE DATES · 2026</p><h2 id="calendar-title">月历</h2></div><div className="month-switcher"><button type="button" aria-label="上一个月" onClick={() => setCalendarMonth((month) => month === 1 ? 12 : month - 1)}>←</button><span>{monthNames[calendarMonth - 1]} 2026</span><button type="button" aria-label="下一个月" onClick={() => setCalendarMonth((month) => month === 12 ? 1 : month + 1)}>→</button></div></header>
        <div className="calendar-layout"><div className="calendar-grid" role="grid" aria-label={`${calendarMonth} 月日历`}><div className="weekdays">{weekdayNames.map((day) => <span key={day}>{day}</span>)}</div><div className="dates">{Array.from({ length: firstWeekday }, (_, index) => <span className="blank-day" key={`blank-${index}`} />)}{Array.from({ length: monthDays }, (_, index) => { const day = index + 1; const entry = monthEntries.find((scientist) => scientist.day === day); return <button className={`date-cell ${entry ? `has-entry ${entry.id === selected.id ? "selected" : ""}` : ""}`} type="button" key={day} onClick={() => entry && selectScientist(entry)} disabled={!entry} aria-label={entry ? `${day} 日：${entry.name}` : `${day} 日没有收录人物`}><span>{day}</span>{entry && <i className={`dot ${entry.color}`} />}</button>; })}</div></div>
          <aside className="calendar-notes"><p className="eyebrow">THIS MONTH</p><h3>{monthEntries.length ? `${monthEntries.length} 个科学瞬间` : "正在整理中"}</h3>{monthEntries.length ? monthEntries.map((entry) => <button className="month-entry" type="button" key={entry.id} onClick={() => selectScientist(entry)}><span>{String(entry.day).padStart(2, "0")}</span><div><strong>{entry.name}</strong><small>{entry.relation} · {entry.field}</small></div><b>↗</b></button>) : <p>这一页将留给新的好奇心。</p>}<p className="calendar-tip">带有彩色圆点的日期，收录了一则科学人物或科学史纪念。</p></aside></div>
      </section>

      <section className="explore-section" id="explore" aria-labelledby="explore-title">
        <header className="section-heading explore-heading"><div><p className="eyebrow">THE ARCHIVE · {scientists.length} STARTING POINTS</p><h2 id="explore-title">从好奇出发</h2></div><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索人物、领域或贡献" aria-label="搜索科学家档案" /></label></header>
        <div className="field-filters" aria-label="按科学领域筛选">{fields.map((field) => <button key={field} type="button" className={field === activeField ? "active" : ""} onClick={() => setActiveField(field)}>{field}</button>)}</div>
        <div className="archive-toolbar" aria-live="polite"><p>当前显示 <strong>{filtered.length}</strong> / {scientists.length} 位人物{activeField !== "全部" ? ` · ${activeField}` : ""}{query.trim() ? ` · “${query.trim()}”` : ""}</p>{(activeField !== "全部" || query) && <button type="button" onClick={() => { setActiveField("全部"); setQuery(""); }}>清除筛选</button>}</div>
        <div className="archive-grid">{filtered.map((scientist, index) => <button className={`archive-card tone-${scientist.color}`} type="button" key={scientist.id} onClick={() => selectScientist(scientist)}><span className="archive-date">{String(scientist.month).padStart(2, "0")}.{String(scientist.day).padStart(2, "0")}</span><span className="archive-art" aria-hidden="true"><i /><b>{scientist.name.slice(0, 1)}</b><em>{scientist.field}</em></span><span className="archive-field">{scientist.field}</span><h3>{scientist.name}</h3><p>{scientist.tagline}</p><span className="archive-open">阅读档案 <b>↗</b></span><i className="archive-index">{String(index + 1).padStart(2, "0")}</i></button>)}</div>
        {!filtered.length && <p className="empty-state">没有找到匹配的人物。换个关键词试试。</p>}
      </section>

      <section className="manifesto" id="about"><p className="eyebrow">WHY A SCIENCE CALENDAR</p><p>科学并非一串遥远的姓名与年份，<br />而是一代代人对世界的<strong>耐心注视</strong>。</p><span>收藏今天的好奇，明天继续提问。</span></section>

      <footer><a className="brand" href="#top"><span className="brand-mark">∴</span> 科学家日历</a><p>精选 {scientists.length} 位人物档案 · 持续更新中</p><a className="footer-download" href={`print/科学家日历_精选${scientists.length}位_A4打印版.pdf`} download>下载 A4 打印版 ↓</a><a href="#top">回到顶部 ↑</a></footer>
    </main>
  );
}
