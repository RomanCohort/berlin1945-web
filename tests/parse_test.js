var S = { visited: [], loc: '', turn: 0, ap: 0, weather: '', gauges: {},
          sector: null, tasks: [], combat: null };
  //         所以别在这里引用 DOM 或其它外部变量（只依赖 S 和正则）。
  function num(re, s, i) { var m = s.match(re); return m ? Number(m[i || 1]) : null; }

  function parseLine(l) {
    var m;
    // 方括号那两行（回合 / 资源总览）
    if (l.charAt(0) === '[') {
      m = l.match(/^\[回合(\d+) \| 行动(\d+) \| ([^|\]]+) \| 天气(\S+)\]/);
      if (m) {
        S.turn = Number(m[1]); S.ap = Number(m[2]);
        S.loc = m[3].trim(); S.weather = m[4];
        if (S.visited[S.visited.length - 1] !== S.loc) { S.visited.push(S.loc); }
        return true;
      }
    }
    if (l.indexOf('[燃油') === 0) {
      var g = {};
      g.fuel = [num(/燃油(\d+)/, l), num(/燃油\d+\/(\d+)/, l)];
      g.mg = [num(/机枪弹(\d+)/, l), num(/机枪弹\d+\/(\d+)/, l)];
      g.ap = [num(/炮弹AP(\d+)/, l), num(/炮弹AP\d+\/(\d+)/, l)];
      g.he = [num(/炮弹AP\d+\/\d+ HE(\d+)/, l), num(/HE(\d+)\/\d+/, l)];
      g.morale = [num(/士气(\d+)/, l), num(/士气\d+\/(\d+)/, l)];
      g.damage = [num(/损伤(\d+)/, l), num(/损伤\d+\/(\d+)/, l)];
      g.collapse = [num(/崩溃(\d+)/, l), num(/崩溃\d+\/(\d+)/, l)];
      S.gauges = g;
      S.armor = num(/装甲(\d+)/, l);
      S.allyTanks = num(/友军坦克(\d+)/, l);
      S.vp = num(/胜利点(\d+)/, l);
      S.fleeing = num(/逃窜敌人(\d+)/, l);
      S.tankKills = num(/坦克击毁(\d+)/, l);
      var s = l.match(/好感(\d+) 沦陷(\d+) 驻军(\d+)/);
      if (s) { S.sector = { favor: Number(s[1]), fall: Number(s[2]), garrison: Number(s[3]) }; }
      return true;
    }
    // 战斗行：没有方括号，以「战斗回合」开头
    if (l.indexOf('战斗回合') === 0) {
      S.combat = {
        round: num(/战斗回合\s*(\d+)/, l),
        dist: (l.match(/距离([^\s]+)/) || [, ''])[1],
        smoke: num(/烟幕(\d+)/, l), maneuver: num(/机动(\d+)/, l),
        cover: num(/掩护(\d+)/, l), light: num(/照明(\d+)/, l),
        suppress: num(/我方压制(\d+)/, l)
      };
      return true;
    }
    // 任务 / 委托行：以 "-" 开头（这一段原来写在"非方括号"那一支里，
    // 结果被那句 return false 挡在前面，永远走不到 —— 单测抓到的）
    // 用 \u2022 而不是直接把圆点写进正则：页面源码里带非 GBK 字符时，
    // 在 Windows 控制台跑生成器会 UnicodeEncodeError（实测踩过）。
    m = l.match(/^[-\u2022]\s*(.+?)\s*\[(进行中|已完成|失败)\][^0-9]*(\d+)\/(\d+)/);
    if (m) {
      S.tasks.push({ name: m[1].trim(), state: m[2], done: Number(m[3]), need: Number(m[4]) });
      if (S.tasks.length > 40) { S.tasks.shift(); }
      return true;
    }
    return false;
  }
  
var lines = ["[回合1 | 行动3 | 米特街区 | 天气晴]", "[燃油200/200 | 机枪弹400/400 | 炮弹AP40/40 HE40/40 | 士气71/200 | 损伤6/100 | 装甲105 | 友军坦克3 | 胜利点0(无勋章) | 崩溃10/100 | 好感51 沦陷70 驻军4 | 逃窜敌人0]", "[燃油188/200 | 机枪弹362/400 | 炮弹AP36/40 HE39/40 | 士气64/200 | 损伤22/100 | 装甲98 | 友军坦克2 | 胜利点3(铁十字) | 崩溃18/100 | 好感44 沦陷76 驻军3 | 逃窜敌人2 | 坦克击毁1 成就2]", "- 护送撤离 [进行中] 0/2", "- 肃清敌人 [进行中] 2/2", "战斗回合 3  | 距离480m 烟幕2 机动1 掩护1 照明0 我方压制0"];
lines.forEach(function (l) { parseLine(l); });
if (S.turn !== 1 || S.loc !== '米特街区') { throw new Error('回合/地点没解析到'); }
// 两行总览都喂进去：后一行必须覆盖前一行
if (!S.sector || S.sector.favor !== 44 || S.sector.fall !== 76 || S.sector.garrison !== 3) { throw new Error('战区: ' + JSON.stringify(S.sector)); }
if (S.gauges.fuel[0] !== 188 || S.gauges.he[0] !== 39 || S.gauges.collapse[0] !== 18) { throw new Error('仪表: ' + JSON.stringify(S.gauges)); }
if (S.armor !== 98 || S.vp !== 3 || S.tankKills !== 1) { throw new Error('数值'); }
if (S.tasks.length !== 2 || S.tasks[0].name !== '护送撤离' || S.tasks[0].need !== 2) { throw new Error('任务: ' + JSON.stringify(S.tasks)); }
if (!S.combat || S.combat.dist !== '480m' || S.combat.smoke !== 2) { throw new Error('战斗: ' + JSON.stringify(S.combat)); }
if (S.visited.length !== 1) { throw new Error('路线没记录'); }
console.log('parse ok');
