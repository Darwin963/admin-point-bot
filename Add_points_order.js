if (interaction.customId === "addpoints") {

  const adminRoles = ["1371504032140628088","1092398849299058736","1286654124527456317","1371504049115107450","1286656850871451688","1293197081997086805","1371504063086067782","1092398849684938873"];
  const hasPermission = adminRoles.some(r =>
    interaction.member.roles.cache.has(r)
  );

  if (!hasPermission)
    return interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setColor("Red")
          .setDescription("❌ ما عندك صلاحية")
      ],
      ephemeral: true
    });

  interaction.reply({
    content: "📝 اكتب: @user amount",
    ephemeral: true
  });

}
