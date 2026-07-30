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
  { id: "nobel", month: 12, day: 10, name: "诺贝尔奖日", latinName: "Nobel Prize Day", years: "1901–至今", field: "医学", country: "瑞典", color: "gold", relation: "颁奖日", tagline: "让突破被世界看见", story: "诺贝尔奖通常在 12 月 10 日颁发，纪念阿尔弗雷德·诺贝尔逝世日。", contribution: "跨学科科学奖项", fact: "和平奖在奥斯陆颁发，其他奖项在斯德哥尔摩。" },
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
          <div className="hero-actions"><a className="button-primary" href="#today">阅读今日人物 <span>↓</span></a><a className="button-secondary" href="print/科学家日历_首批30位_A4打印版.pdf" download>获取 A4 打印版 <span>↓</span></a><a className="text-link" href="#calendar">查看月历 <span>→</span></a></div>
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
        <div><strong>12</strong><span>个月的好奇线索</span></div>
        <p>点开任意日期，读一则发现，也留下一点继续提问的余地。</p>
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

      <footer><a className="brand" href="#top"><span className="brand-mark">∴</span> 科学家日历</a><p>精选 {scientists.length} 位人物档案 · 持续更新中</p><a className="footer-download" href="print/科学家日历_精选54位_A4打印版.pdf" download>下载 A4 打印版 ↓</a><a href="#top">回到顶部 ↑</a></footer>
    </main>
  );
}
