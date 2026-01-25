const {
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle
} = require("discord.js");

if (message.content === "points") {

  const embed = new EmbedBuilder()
    .setColor("#5865F2")
    .setTitle("📊 نظام النقاط")
    .setDescription(
      "اختر العملية من الأزرار بالأسفل 👇"
    )
    .setFooter({ text: "GhostCraft Points System" });

  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId("mypoints")
      .setLabel("نقاطي")
      .setStyle(ButtonStyle.Primary),

    new ButtonBuilder()
      .setCustomId("checkpoints")
      .setLabel("معرفة نقاط شخص")
      .setStyle(ButtonStyle.Secondary),

    new ButtonBuilder()
      .setCustomId("addpoints")
      .setLabel("إضافة نقاط")
      .setStyle(ButtonStyle.Success),

    new ButtonBuilder()
      .setCustomId("top")
      .setLabel("Top")
      .setStyle(ButtonStyle.Danger)
  );

  message.channel.send({ embeds: [embed], components: [row] });
}
