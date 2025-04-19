window.addEventListener("DOMContentLoaded", async () => {
  // 當整個 HTML DOM 結構載入完成後才執行這段程式
  const token = localStorage.getItem("token");
  // 取得本地儲存的 token

  if (!token) {
    // 若沒有 token（未登入）
    window.location.href = "/"; // 導回首頁
    return;
  }

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

  // week14
  const APP_ID = "159811"; // TapPay 提供的 App ID
  const APP_KEY = // TapPay 提供的 App Key
    "app_WWvK8HynAyfYWeZGF00Tay26QW9vJZGpTDS3Y5XCXSSm8CNKuDVT5vo1JbxE";
  TPDirect.setupSDK(APP_ID, APP_KEY, "sandbox");
  // 初始化 TapPay SDK，sandbox 表示測試環境

  let fields = {
    // 設定信用卡欄位，綁定對應的 DOM 元素，這些會被 TapPay 接管
    number: {
      element: "#card-number",
      placeholder: "**** **** **** ****",
    },
    expirationDate: {
      element: document.getElementById("card-expiration-date"),
      placeholder: "MM / YY",
    },
    ccv: {
      element: "#card-ccv",
      placeholder: "CCV",
    },
  };

  TPDirect.card.setup({
    // 啟用信用卡輸入欄位，套用自訂樣式與遮罩功能
    fields: fields,
    styles: {
      input: {
        color: "gray",
      },
      "input.ccv": {
        color: "black",
        "font-size": "16px",
      },
      "input.expiration-date": {
        color: "black",
        "font-size": "16px",
      },
      "input.card-number": {
        color: "black",
        "font-size": "16px",
      },

      ":focus": {},
      ".valid": {
        color: "green",
        "font-size": "16px",
      },
      ".invalid": {
        color: "red",
        "font-size": "16px",
      },
      "@media screen and (max-width: 400px)": {
        input: {
          color: "orange",
        },
      },
    },
    isMaskCreditCardNumber: true,
    maskCreditCardNumberRange: {
      beginIndex: 6,
      endIndex: 11,
    },
  });

  const submitButton = document.querySelector(".pay");
  console.log("submitButton 是否成功選到：", submitButton); // null 就錯了

  TPDirect.card.onUpdate(function (update) {
    console.log("🔍 card update 狀態：", update); // 加這行

    // 監聽使用者輸入狀況，update 會包含每個欄位的驗證結果與是否可以 getPrime 的狀態

    if (update.canGetPrime) {
      submitButton.removeAttribute("disabled");
    } else {
      submitButton.setAttribute("disabled", true);
    }
    // ✔ 啟用或停用「確認付款」按鈕：
    // 你應該要在這邊控制 .pay 按鈕的 disabled 狀態
    // 這樣可以防止使用者在卡號不完整時就亂按付款。
  });

  // week13
  let bookingData = null;
  let userName = "";
  const payload = jwt_decode(token);
  userName = payload.data.name;
  email = payload.data.email;

  // 解碼 JWT token，取得使用者資料，後續用於顯示及訂單聯絡人欄位。

  // week13
  // fetch bookimg api
  const response = await fetch("/api/booking", {
    //呼叫 /api/booking，取得使用者當前預定資訊
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
  });
  console.log("booking api fetch 完成，response：", response);
  console.log("booking Status code:", response.status); // 這裡會印出 200、400、401、500 之類的

  // 解析 booking api 拿到的資料
  const data = await response.json();
  bookingData = data.data;

  if (bookingData) {
    let textContent = "";
    if (bookingData.time === "上半天") {
      textContent = "早上 9 點到下午 4 點";
    } else {
      textContent = "下午 2 點到晚上 9 點";
    }

    console.log("圖片網址：", bookingData.attraction.images);
    document.querySelector(".img").src = bookingData.attraction.images;
    document.querySelector(".name").textContent = bookingData.attraction.name;
    document.querySelector(".date").textContent = bookingData.date;
    document.querySelector(".time").textContent = textContent;
    document.querySelector(
      ".price"
    ).textContent = `新台幣 ${bookingData.price} 元`;
    document.querySelector(".address").textContent =
      bookingData.attraction.address;
    document.querySelector(".headline-2").textContent = userName;
    document.querySelector(
      "span.total"
    ).textContent = `新台幣 ${bookingData.price} 元`;
    document.querySelector("input.contact-name").value = userName;
    document.querySelector("input.contact-email").value = email;
  } else {
    console.log("目前沒有預定行程");
    document.querySelector(".headline-2").textContent = userName;

    document.querySelector("main.none").innerHTML = `
    <p class="none">目前沒有任何待預訂的行程</p>`;
  }

  // week14
  submitButton.addEventListener("click", (event) => {
    console.log("🔔 付款按鈕點擊了");

    event.preventDefault();
    //綁定付款按鈕事件，阻止預設提交行為

    const tappayStatus = TPDirect.card.getTappayFieldsStatus();
    // TPDirect.card.getTappayFieldsStatus()：這個是 TapPay 提供的函式，用來檢查目前使用者填的卡號、有效日期、CCV 是否都正確

    if (tappayStatus.canGetPrime) {
      submitButton.removeAttribute("disabled");
    }

    if (tappayStatus.canGetPrime === false) {
      alert("can not get prime");
      return;
    }
    // tappayStatus.canGetPrime：這是一個布林值：
    //  - true 代表輸入的資訊都正確，可以產生 Prime。
    //  - false 代表資訊有誤，不能產生 Prime。

    // Get prime
    TPDirect.card.getPrime(async (result) => {
      console.log("✅ getPrime 被呼叫了，result：", result); // 加這行

      if (result.status !== 0) {
        alert("取得 Prime 失敗：" + result.msg);
        return;
      }
      // 這裡就是呼叫 TapPay 提供的 API 函式 getPrime()，它會：
      // 向 TapPay 的伺服器發送請求，將使用者輸入的卡號等資訊加密成一個一次性代碼。
      // 回傳結果包含：
      //  - result.status：狀態碼，0 代表成功。
      //  - result.card.prime：這就是 TapPay 回傳給你的 Prime（一次性付款憑證）。
      // 💡 Prime 的作用：你不會拿到卡號，也不需要管卡號的安全，只要把這個 prime 傳給後端，它就可以代表那張卡來做付款。
      try {
        const prime = result.card.prime;
        const phone = document.querySelector("input.contact-phone").value;

        const orderData = {
          prime: prime,
          order: {
            price: bookingData.price,
            trip: {
              attraction: {
                id: bookingData.attraction.id,
                name: bookingData.attraction.name,
                address: bookingData.attraction.address,
                image: bookingData.attraction.image,
              },
              date: bookingData.date,
              time: bookingData.time,
            },
            contact: {
              name: userName,
              email: email,
              phone: phone,
            },
          },
        };

        console.log("取得的 Prime：", result.card.prime);
        console.log("要傳送的 orderData：", orderData);

        await fetch("/api/order", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + token,
          },
          body: JSON.stringify(orderData),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.ok) {
              window.location.href = `/thankyou?orderNumber=${data.order_number}`;
            } else {
              alert("付款失敗：" + data.message);
            }
          });
      } catch (error) {
        console.log("訂單建立失敗", error);
      }
    });
  });

  // 綁定刪除預約按鈕，呼叫 /api/booking DELETE，成功後重新整理畫面
  document.querySelector(".delete").addEventListener("click", async () => {
    const token = localStorage.getItem("token"); // 確保有 token

    const response = await fetch("/api/booking", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
    });

    if (response.ok) {
      location.reload();
      console.log("刪除成功！");
    } else {
      console.log("刪除失敗！");
    }
  });
});
