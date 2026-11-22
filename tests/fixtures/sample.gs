// Google Apps Script
function getWallets() {
  var url = "https://api.bitpanda.com/v1/wallets";
  var opts = {headers: {"X-API-KEY": PropertiesService.getScriptProperties().getProperty("BP")}};
  return UrlFetchApp.fetch(url, opts);
}
function getTrades() {
  return UrlFetchApp.fetch("https://api.bitpanda.com/v1/trades?page_size=100");
}
