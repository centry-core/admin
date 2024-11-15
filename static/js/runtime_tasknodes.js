$(".refresh-table-button").click(function() {
  $($(this).data("target")).bootstrapTable("refresh", {});
});
