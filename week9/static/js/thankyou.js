document.querySelector(".appointment").addEventListener("click", () => {
  console.log("點擊到按鈕了！");
  const token = localStorage.getItem("token");
  if (!token) {
    signUpFormContainer.style.display = "block";
    popUpArea.style.display = "block";
  } else {
    window.location.href = "/booking";
  }
});

console.log("URL:", window.location.href); // 打印出當前完整 URL
console.log("search params:", window.location.search); // 打印出查詢字符串

const params = new URLSearchParams(window.location.search);
const orderNumber = params.get("orderNumber");
console.log("訂單標號是：", orderNumber);

document.querySelector(".order_number").textContent = orderNumber;



// 建立環境變數：mysql帳密, jwt_key, partner_key,marchant_id, 前端的資訊都無法藏起來
