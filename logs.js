const {
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle
} = require("discord.js");

const { QuickDB } = require("quick.db");
const db = new QuickDB();

// ====== الإعدادات ======
const ADMIN_ROLES = [
  "1371504032140628088",
  "1092398849299058736",
  "1286654124527456317",
  "1371504049115107450",
  "1286656850871451688",
  "1293197081997086805",
  "1371504063086067782",
  "1092398849684938873"
];

const LOG_CHANNEL_ID = "1463173288653099041";
// =======================


// ====== دالة التحقق من الصلاحية ======
function hasAdminRole(member) {
  return ADMIN_ROLES.some(roleId =>
    member.roles.cache.has(roleId)
  );
}

// ====== دالة إرسال اللوق ======
function sendPointsLog({ type, guild, admin, target, amount, total }) {
  const logChannel = guild.channels.cache.get(LOG_CHANNEL_ID);
  if (!logChannel) return;

  const embed = new EmbedBuilder()
    .setColor(type === "add" ? "#00ff99" : "#ff5555")
    .setTitle(type === "add" ? "➕ إضافة نقاط" : "➖ خصم نقاط")
    .addFields(
      { name: "👤 الإداري", value: `${admin} (${admin.id})` },
      { name: "👥 العضو", value: `${target} (${target.id})` },
      { name: "🔢 الكمية", value: `${amount}` },
      { name: "📊 المجموع الجديد", value: `${total}` }
    )
    .setTimestamp();

  logChannel.send({ embeds: [embed] });
}

// ====== لوحة الأزرار ======
if (message.content === "points") {

  const embed = new EmbedBuilder()
    .setColor("#5865F2")
    .setTitle("📊 نظام النقاط")
    .setDescription("اختر من الأزرار بالأسفل 👇");

  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId("add_points")
      .setLabel("➕ إضافة نقاط")
      .setStyle(ButtonStyle.Success),

    new ButtonBuilder()
      .setCustomId("remove_points")
      .setLabel("➖ خصم نقاط")
      .setStyle(ButtonStyle.Danger)
  );

  message.channel.send({ embeds: [embed], components: [row] });
}

// ====== التفاعل مع الأزرار ======
client.on("interactionCreate", async interaction => {
  if (!interaction.isButton()) return;

  // تحقق من الصلاحية
  if (!hasAdminRole(interaction.member)) {
    return interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setColor("Red")
          .setDescription("❌ ما عندك صلاحية")
      ],
      ephemeral: true
    });
  }

  await interaction.reply({
    content: "📝 اكتب في الشات:\n@user amount",
    ephemeral: true
  });

  const filter = m =>
    m.author.id === interaction.user.id &&
    m.mentions.users.first();

  const collected = await interaction.channel.awaitMessages({
    filter,
    max: 1,
    time: 30000
  });

  if (!collected.size) return;

  const msg = collected.first();
  const user = msg.mentions.users.first();
  const amount = parseInt(msg.content.split(" ")[1]);

  if (!amount || amount <= 0) {
    return interaction.followUp({
      content: "❌ رقم غير صحيح",
      ephemeral: true
    });
  }

  const key = `points_${user.id}`;
  let total;

  // ➕ إضافة نقاط
  if (interaction.customId === "add_points") {
    await db.add(key, amount);
    total = await db.get(key);

    sendPointsLog({
      type: "add",
      guild: interaction.guild,
      admin: interaction.user,
      target: user,
      amount,
      total
    });

    interaction.followUp({
      embeds: [
        new EmbedBuilder()
          .setColor("#00ff99")
          .setDescription(`✅ تم إضافة **${amount}** نقطة لـ ${user}`)
      ],
      ephemeral: true
    });
  }

  // ➖ خصم نقاط
  if (interaction.customId === "remove_points") {
    await db.subtract(key, amount);
    total = await db.get(key);
    if (total < 0) {
      await db.set(key, 0);
      total = 0;
    }

    sendPointsLog({
      type: "remove",
      guild: interaction.guild,
      admin: interaction.user,
      target: user,
      amount,
      total
    });

    interaction.followUp({
      embeds: [
        new EmbedBuilder()
          .setColor("#ff5555")
          .setDescription(`✅ تم خصم **${amount}** نقطة من ${user}`)
      ],
      ephemeral: true
    });
  }
});
