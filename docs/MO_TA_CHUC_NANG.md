# MÔ TẢ CÁC CHỨC NĂNG CỦA CHƯƠNG TRÌNH

---

## 1. Tổng quan hệ thống

Hệ thống Quản lý Đại lý Xe hơi bao gồm 15 module nghiệp vụ chính với tổng cộng 71 chức năng được thiết kế để phục vụ toàn bộ hoạt động kinh doanh của một đại lý xe hơi. Các module được tổ chức theo luồng công việc thực tế, bắt đầu từ quản lý hàng tồn kho, thông qua các nghiệp vụ bán hàng và hậu mãi, cho đến báo cáo tổng hợp và bảo mật hệ thống. Mỗi module có chức năng riêng biệt nhưng đều liên kết với nhau thông qua dữ liệu chia sẻ, tạo thành một hệ thống thống nhất và đồng bộ.

Hệ thống sử dụng mô hình Clean Architecture với bốn tầng rõ ràng. Tầng presentation chứa toàn bộ giao diện PyQt6, tầng application chứa các service xử lý nghiệp vụ, tầng domain chứa các entity và business rules, và tầng infrastructure chứa repository và các thư viện bên ngoài. Dữ liệu được lưu trữ tập trung trong SQLite với quan hệ khóa ngoại giữa các bảng đảm bảo tính toàn vẹn dữ liệu.

---

## 2. Bảng tổng hợp các module chức năng

| Module                      | Số chức năng | Phạm vi nghiệp vụ                                               |
| --------------------------- | ------------ | --------------------------------------------------------------- |
| Quản lý thông tin xe        | 5            | Thêm, sửa, xóa, tìm kiếm, lọc xe trong kho                     |
| Quản lý khách hàng          | 4            | Hồ sơ, phân loại, lịch sử giao dịch                            |
| Quản lý nhân viên           | 5            | Quản lý nhân viên, KPI, thông tin cá nhân                       |
| Quản lý hợp đồng bán xe     | 6            | Tạo hợp đồng, tính giá, phụ kiện, khuyến mãi, trạng thái, in PDF |
| Quản lý kho xe              | 3            | Cập nhật tồn kho, cảnh báo, lịch sử nhập                        |
| Quản lý bảo hành            | 7            | Ghi nhận, lịch sử, cảnh báo, tiếp nhận, phân loại, in, thống kê |
| Quản lý khuyến mãi          | 7            | Tạo, loại, phạm vi, mức giảm, theo dõi, tự động áp dụng, trạng thái |
| Quản lý phụ kiện            | 5            | Danh mục, phân loại, cảnh báo, combo, thêm vào hợp đồng         |
| Dịch vụ hậu mãi             | 4            | Lịch bảo dưỡng, lịch sử, cứu hộ, chăm sóc khách hàng           |
| Quản lý nhà cung cấp        | 4            | Thông tin, lịch sử, đánh giá, đơn đặt hàng                      |
| Quản lý trả góp             | 4            | Thông tin trả góp, tính toán, theo dõi, cảnh báo               |
| Quản lý marketing           | 4            | Chiến dịch, hiệu quả, sự kiện, lead                             |
| Quản lý khiếu nại           | 5            | Ghi nhận, phân công, theo dõi, đánh giá, báo cáo               |
| Báo cáo thống kê            | 4            | Doanh thu, top xe, KPI nhân viên, khách hàng VIP              |
| Hệ thống bảo mật            | 4            | Đăng nhập, mã hóa, ghi log, session timeout                    |
| **Tổng cộng**               | **71**       | Toàn bộ hệ thống                                                |

---

## 3. Chi tiết từng module

### 3.1. Module quản lý thông tin xe

Module quản lý thông tin xe là nơi xuất phát của hầu hết các quy trình kinh doanh trong hệ thống. Toàn bộ thông tin về các xe có trong kho đại lý được quản lý tại đây, bao gồm mã xe, hãng sản xuất, dòng xe, năm sản xuất, màu sắc, giá bán và số lượng tồn kho. Khi nhập kho xe mới, nhân viên nhập đầy đủ thông tin xe vào hệ thống và xe ngay lập tức xuất hiện trong danh sách xe có sẵn để bán. Hệ thống hỗ trợ tìm kiếm nâng cao cho phép kết hợp nhiều tiêu chí như hãng xe kết hợp mức giá, năm sản xuất kết hợp màu sắc, giúp nhân viên nhanh chóng tìm được xe phù hợp yêu cầu của khách hàng. Việc chỉnh sửa thông tin xe cho phép cập nhật mọi trường trừ mã xe vì mã xe là định danh duy nhất dùng để phân biệt các sản phẩm. Xe chỉ có thể xóa khi chưa có bất kỳ hợp đồng nào liên quan, nếu không hệ thống sẽ từ chối xóa và yêu cầu hủy liên kết hợp đồng trước.

### 3.2. Module quản lý khách hàng

Module quản lý khách hàng lưu trữ toàn bộ thông tin về khách hàng đã mua xe hoặc tiềm năng của đại lý. Mỗi khách hàng có họ tên, số điện thoại và email là các trường bắt buộc phải nhập khi tạo hồ sơ. Số điện thoại phải là duy nhất trong hệ thống vì được sử dụng để định danh khách hàng và gửi tin nhắn nhắc nhở bảo dưỡng. Hệ thống tự động phân loại khách hàng dựa trên tổng giá trị mua hàng và số lần giao dịch thành các hạng khác nhau, giúp đại lý nhận biết được nhóm khách hàng quan trọng và đưa ra chương trình chăm sóc phù hợp. Lịch sử giao dịch của khách hàng hiển thị đầy đủ tất cả các hợp đồng đã tạo, bao gồm cả hợp đồng đã hủy, giúp nhân viên hiểu rõ hành vi mua sắm của từng khách hàng để tư vấn hiệu quả hơn. Khi khách hàng đã có hợp đồng liên quan, việc xóa không được phép mà chỉ có thể đánh dấu khách hàng là không còn hoạt động để giữ lại lịch sử.

### 3.3. Module quản lý nhân viên

Module quản lý nhân viên phục vụ cho việc quản trị nhân sự trong đại lý. Chỉ quản trị viên mới có quyền thêm mới, chỉnh sửa và xóa nhân viên. Mỗi nhân viên có thông tin cá nhân bao gồm họ tên, email, số điện thoại, địa chỉ và vai trò trong hệ thống. Nhân viên bán hàng có thể đăng nhập và xem thông tin cá nhân của mình bao gồm số hợp đồng đã tạo và doanh thu đã đóng góp. Hệ thống theo dõi KPI cho từng nhân viên bao gồm số xe bán được và tổng doanh thu tạo ra, là cơ sở để đánh giá hiệu quả công việc và tính hoa hồng. Các vai trò trong hệ thống được phân biệt rõ ràng với mã vai trò A-01 cho quản trị viên, A-02 cho nhân viên bán hàng và A-03 cho nhân viên kỹ thuật bảo hành, mỗi vai trò có quyền truy cập và thao tác khác nhau trên hệ thống.

### 3.4. Module quản lý hợp đồng bán xe

Module quản lý hợp đồng bán xe là module trọng tâm của toàn bộ hệ thống, nơi diễn ra giao dịch chính của đại lý. Khi tạo hợp đồng mới, nhân viên chọn xe từ kho, nhập thông tin khách hàng và hệ thống tự động tính toán giá trị hợp đồng bao gồm giá xe cộng các phụ kiện đi kèm trừ đi các khuyến mãi áp dụng. Hệ thống hỗ trợ hai hình thức thanh toán chính là thanh toán một lần và trả góp qua ngân hàng hoặc công ty tài chính. Với hình thức trả góp, hệ thống tính toán số tiền trả hàng tháng dựa trên số tiền vay, lãi suất và thời hạn vay. Trạng thái hợp đồng thay đổi theo tiến độ từ mới tạo sang đã thanh toán và đã giao xe, hoặc bị hủy nếu giao dịch không thành. Hợp đồng có thể được xuất ra file PDF chuyên nghiệp với đầy đủ thông tin về xe, khách hàng, giá trị và các điều khoản thanh toán.

**Sơ đồ luồng tạo hợp đồng bán xe:**

```
Nhân viên đăng nhập
        │
        ▼
Chọn tạo hợp đồng mới
        │
        ▼
Chọn xe từ kho (kiểm tra còn hàng)
        │
        ▼
Nhập / chọn thông tin khách hàng
        │
        ▼
Thêm phụ kiện vào hợp đồng (tùy chọn)
        │
        ▼
Hệ thống tự động áp dụng khuyến mãi phù hợp
        │
        ▼
Tính toán giá trị hợp đồng tổng cộng
        │
        ▼
Chọn hình thức thanh toán (một lần / trả góp)
        │
        ├─── Thanh toán một lần ── Lưu hợp đồng ── Cập nhật trạng thái xe
        │
        └─── Thanh toán trả góp ── Tính số tiền hàng tháng ── Lưu thông tin trả góp
                                                     │
                                                     ▼
                                              Lưu hợp đồng ── Cập nhật trạng thái xe
        │
        ▼
Xuất hợp đồng PDF (tùy chọn)
        │
        ▼
Hoàn tất
```

### 3.5. Module quản lý kho xe

Module quản lý kho xe theo dõi và cập nhật số lượng xe tồn trong kho của đại lý. Hệ thống tự động cập nhật số lượng tồn kho mỗi khi có hợp đồng mới được tạo hoặc hủy bỏ. Khi xe được bán, trạng thái của xe tự động chuyển từ còn hàng sang đã bán và không còn hiển thị trong danh sách xe khả dụng. Ngược lại, khi hợp đồng bị hủy, xe được hoàn trả về trạng thái còn hàng. Hệ thống cung cấp cảnh báo tồn kho thấp khi số lượng xe của một dòng xe nào đó giảm xuống dưới mức tối thiểu do đại lý thiết lập, giúp quản lý kịp thời nhập thêm xe mới từ nhà cung cấp. Lịch sử nhập kho ghi nhận chi tiết từng lần nhập hàng bao gồm ngày nhập, nhà cung cấp, số lượng và giá nhập, tạo cơ sở để đối chiếu và theo dõi chuỗi cung ứng của đại lý.

### 3.6. Module quản lý bảo hành

Module quản lý bảo hành xử lý tất cả các yêu cầu liên quan đến bảo hành xe sau khi bán. Mỗi xe khi được bán đều có thời hạn bảo hành tính bằng tháng và phạm vi bảo hành được ghi nhận trong hệ thống. Khi khách hàng mang xe đến bảo hành, nhân viên tiếp nhận yêu cầu và hệ thống kiểm tra xem xe còn trong thời hạn bảo hành hay không và sự cố có nằm trong phạm vi bảo hành hay không. Yêu cầu bảo hành được phân loại thành miễn phí hoặc tính phí dựa trên kết quả kiểm tra. Lịch sử bảo hành được theo dõi chi tiết theo từng xe và từng khách hàng, giúp đại lý có dữ liệu để phân tích chất lượng sản phẩm và dịch vụ. Hệ thống cảnh báo trước 30 ngày khi bảo hành của một xe sắp hết hạn, tạo cơ hội để nhân viên chủ động liên hệ khách hàng mời quay lại bảo dưỡng. Phiếu bảo hành và biên lai sửa chữa có thể được in ra từ hệ thống với định dạng PDF chuyên nghiệp.

### 3.7. Module quản lý khuyến mãi

Module quản lý khuyến mãi cho phép đại lý tạo và quản lý các chương trình khuyến mãi nhằm kích thích doanh số. Mỗi chương trình khuyến mãi có tên, mô tả, thời gian bắt đầu và kết thúc, loại khuyến mãi có thể là giảm tiền mặt, giảm phần trăm, tặng phụ kiện, giảm lãi suất trả góp hoặc combo khuyến mãi. Phạm vi áp dụng cho phép giới hạn khuyến mãi theo toàn bộ xe, theo hãng cụ thể, theo dòng xe cụ thể, hoặc chỉ áp dụng cho xe tồn kho lâu ngày cần ưu đãi đặc biệt để giải phóng vốn. Mức giảm giá có thể là số tiền cố định hoặc phần trăm của giá xe. Hệ thống tự động áp dụng khuyến mãi phù hợp khi nhân viên tạo hợp đồng mới nếu xe thỏa mãn điều kiện của chương trình, giúp nhân viên không phải nhớ và tính toán thủ công. Đại lý có thể theo dõi hiệu quả của từng chương trình khuyến mãi thông qua số xe bán ra và doanh thu từ khuyến mãi, đồng thời có thể tạm dừng hoặc dừng hẳn một chương trình khi cần.

### 3.8. Module quản lý phụ kiện

Module quản lý phụ kiện quản lý danh mục các sản phẩm phụ kiện đi kèm xe như nội thất, ngoại thất, thiết bị điện tử, sản phẩm bảo vệ và vật phẩm trang trí. Mỗi phụ kiện có tên, mô tả, giá bán và số lượng tồn kho. Phụ kiện được phân loại theo nhóm để dễ dàng tìm kiếm và quản lý. Hệ thống cảnh báo khi tồn kho phụ kiện cạn kiệt, giúp nhân viên kịp thời đặt hàng nhà cung cấp. Đại lý có thể tạo các gói combo phụ kiện với giá ưu đãi so với việc mua lẻ từng sản phẩm, khuyến khích khách hàng mua nhiều phụ kiện hơn. Khi tạo hợp đồng, nhân viên có thể thêm phụ kiện vào đơn hàng và giá của phụ kiện được tính riêng biệt trong hợp đồng.

### 3.9. Module dịch vụ hậu mãi

Module dịch vụ hậu mãi bao gồm các chức năng chăm sóc khách hàng sau khi bán xe. Lịch bảo dưỡng định kỳ được thiết lập dựa trên số kilômét đã chạy hoặc số tháng sử dụng tùy theo loại dịch vụ, và hệ thống tự động nhắc nhở khách hàng trước khi đến hạn bảo dưỡng. Lịch sử bảo dưỡng ghi nhận đầy đủ thông tin về ngày mang xe đến, nội dung dịch vụ đã thực hiện và chi phí phát sinh, tạo hồ sơ bảo dưỡng đầy đủ cho từng xe. Module cứu hộ ghi nhận các yêu cầu hỗ trợ kỹ thuật khẩn cấp bao gồm thông tin liên hệ, mô tả sự cố, phản hồi từ đại lý và chi phí xử lý. Chức năng chăm sóc khách hàng bao gồm việc gửi thiệp chúc mừng sinh nhật và các chương trình ưu đãi tri ân khách hàng lâu năm.

### 3.10. Module quản lý nhà cung cấp

Module quản lý nhà cung cấp lưu trữ thông tin và theo dõi hiệu quả làm việc với các đối tác cung cấp xe và phụ kiện cho đại lý. Thông tin nhà cung cấp bao gồm tên công ty, địa chỉ, số điện thoại, email và thông tin người liên hệ. Lịch sử nhập hàng từ mỗi nhà cung cấp được ghi nhận chi tiết bao gồm ngày nhập, số lượng và giá nhập, tạo cơ sở để so sánh giá giữa các nhà cung cấp. Hệ thống đánh giá nhà cung cấp dựa trên ba tiêu chí chính là chất lượng sản phẩm, thời gian giao hàng và mức giá cung cấp, giúp đại lý có căn cứ để lựa chọn nhà cung cấp phù hợp. Khi cần đặt hàng mới, nhân viên có thể tạo đơn đặt hàng trực tiếp từ hệ thống và gửi cho nhà cung cấp.

### 3.11. Module quản lý trả góp

Module quản lý trả góp xử lý các nghiệp vụ liên quan đến hình thức thanh toán trả góp khi khách hàng mua xe. Thông tin trả góp bao gồm tên ngân hàng hoặc công ty tài chính, số tiền vay ban đầu, lãi suất hàng năm và thời hạn vay tính bằng tháng. Hệ thống tính toán số tiền trả hàng tháng dựa trên công thức tính toán tài chính chuẩn, bao gồm cả phần gốc và phần lãi trong mỗi kỳ thanh toán. Sau khi hợp đồng trả góp được tạo, hệ thống theo dõi tiến độ thanh toán của từng khách hàng với thông tin số tiền còn nợ và số kỳ còn lại. Khi khách hàng thanh toán trễ hạn hơn 5 ngày, hệ thống tự động gửi cảnh báo để nhân viên chủ động liên hệ và nhắc nhở khách hàng.

### 3.12. Module quản lý marketing

Module quản lý marketing hỗ trợ các hoạt động tiếp thị và thu hút khách hàng tiềm năng của đại lý. Chiến dịch marketing được tạo với thông tin về tên chiến dịch, ngân sách dự kiến, thời gian chạy chiến dịch và các kênh tiếp thị được sử dụng như mạng xã hội, website, email hoặc sự kiện trực tiếp. Hệ thống theo dõi hiệu quả chiến dịch thông qua các chỉ số về số lượng khách hàng tiềm năng được tạo và tỷ lệ chuyển đổi thành khách hàng thực tế. Lead (khách hàng tiềm năng) được quản lý từ nhiều nguồn khác nhau bao gồm quảng cáo online, giới thiệu và sự kiện, với thông tin liên hệ và trạng thái xử lý được cập nhật liên tục. Quản lý sự kiện cho phép đại lý lên kế hoạch và theo dõi các hoạt động lái thử xe và triển lãm xe mới.

### 3.13. Module quản lý khiếu nại

Module quản lý khiếu nại tiếp nhận và xử lý các phản ánh của khách hàng về chất lượng sản phẩm hoặc dịch vụ của đại lý. Mỗi khiếu nại được ghi nhận với nội dung chi tiết, ngày tiếp nhận và mức độ ưu tiên được phân loại thành thấp, trung bình hoặc cao. Hệ thống cho phép phân công khiếu nại cho nhân viên phụ trách xử lý và theo dõi tiến độ xử lý qua các trạng thái đang xử lý, đã giải quyết hoặc đã đóng. Khi khiếu nại được xử lý xong, khách hàng được khảo sát mức độ hài lòng để đại lý đánh giá chất lượng dịch vụ. Báo cáo khiếu nại tổng hợp theo loại khiếu nại và theo thời gian giúp quản lý nhận diện các vấn đề phổ biến và cải thiện quy trình dịch vụ.

### 3.14. Module báo cáo thống kê

Module báo cáo thống kê cung cấp các công cụ phân tích dữ liệu cho quản lý đại lý. Báo cáo doanh thu cho phép xem tổng doanh thu theo các khoảng thời gian khác nhau như ngày, tháng hoặc năm, với khả năng phân tích chi tiết theo từng dòng xe hoặc từng nhân viên bán hàng. Báo cáo top xe bán chạy thống kê và xếp hạng các mẫu xe có doanh số cao nhất, giúp đại lý đưa ra quyết định về số lượng nhập kho cho từng dòng xe. Báo cáo KPI nhân viên hiển thị thành tích của từng nhân viên bao gồm số xe bán được, doanh thu tạo ra và so sánh với mục tiêu đề ra. Báo cáo khách hàng VIP xếp hạng khách hàng theo tổng giá trị mua hàng tích lũy, giúp đại lý xác định nhóm khách hàng quan trọng nhất để có chương trình chăm sóc phù hợp. Các báo cáo có thể được xuất ra định dạng Excel để phân tích sâu hơn hoặc chia sẻ với các bộ phận khác.

### 3.15. Module hệ thống bảo mật

Module hệ thống bảo mật đảm bảo an toàn cho toàn bộ hoạt động của hệ thống. Chức năng đăng nhập yêu cầu người dùng nhập tài khoản và mật khẩu để truy cập hệ thống, với việc xác thực thông tin đăng nhập được thực hiện thông qua so sánh mật khẩu đã băm bằng bcrypt. Mật khẩu được mã hóa bằng thuật toán bcrypt với chi phí tính toán cao, đảm bảo rằng ngay cả khi cơ sở dữ liệu bị lộ, mật khẩu gốc của người dùng cũng không thể bị khôi phục. Hệ thống ghi log tất cả các hoạt động quan trọng bao gồm đăng nhập, đăng xuất, tạo mới, chỉnh sửa và xóa dữ liệu, tạo cơ sở để kiểm toán và truy vết khi có sự cố. Sau 30 phút không thao tác, phiên đăng nhập tự động hết hạn và người dùng phải đăng nhập lại để tiếp tục sử dụng hệ thống, ngăn chặn truy cập trái phép khi máy tính bị bỏ mà không khóa. Tài khoản bị khóa tạm thời khi nhập sai mật khẩu 5 lần liên tiếp để ngăn chặn tấn công brute-force.

---

## 4. Sơ đồ quan hệ giữa các module chính

Sơ đồ dưới đây thể hiện mối quan hệ và luồng dữ liệu giữa các module trong hệ thống:

```
                    ┌─────────────────┐
                    │   Quản lý Kho   │
                    │      Xe         │
                    └────────┬────────┘
                             │ Cung cấp xe cho
                             ▼
                    ┌─────────────────┐
                    │  Quản lý Hợp   │◄───────────────┐
                    │   đồng Bán Xe   │                │
                    └────────┬────────┘                │
                             │                         │
          ┌──────────────────┼──────────────────┐      │
          │                  │                  │      │
          ▼                  ▼                  ▼      │
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
   │  Quản lý    │   │  Quản lý    │   │  Quản lý    │  │
   │  Khách hàng │   │  Trả góp    │   │  Khuyến mãi │  │
   └─────────────┘   └─────────────┘   └─────────────┘  │
          │                  │                  │         │
          │                  ▼                  │         │
          │           ┌─────────────┐          │         │
          │           │ Theo dõi    │          │         │
          │           │ tiến độ TT  │          │         │
          │           └─────────────┘          │         │
          │                                    │         │
          ▼                                    ▼         │
   ┌─────────────┐                      ┌─────────────┐  │
   │  Quản lý    │                      │  Quản lý    │  │
   │  Bảo hành   │──────────────────────│  Phụ kiện   │  │
   └─────────────┘                      └─────────────┘  │
          │                                    │         │
          ▼                                    │         │
   ┌─────────────┐                             │         │
   │  Dịch vụ    │                             │         │
   │  Hậu mãi    │                             │         │
   └─────────────┘                             │         │
          │                                    │         │
          ▼                                    │         │
   ┌─────────────┐                             │         │
   │  Quản lý    │◄────────────────────────────┘         │
   │  Khiếu nại  │                                    │
   └─────────────┘                                    │
          │                                           │
          ▼                                           │
   ┌─────────────┐                                    │
   │   Báo cáo   │◄───────────────────────────────────┘
   │  Thống kê   │
   └─────────────┘
          ▲
          │
   ┌─────────────┐
   │  Hệ thống   │
   │  Bảo mật    │
   └─────────────┘
```

---

## 5. Sơ đồ luồng nghiệp vụ tổng thể

Sơ đồ dưới đây thể hiện các luồng nghiệp vụ chính từ khi tiếp nhận xe vào kho cho đến khi hoàn thành tất cả các dịch vụ hậu mãi:

```
LUỒNG 1: NHẬP KHO XE MỚI
Nhà cung cấp giao xe ──► Tạo phiếu nhập kho ──► Cập nhật số lượng tồn kho ──► Xe sẵn sàng bán

LUỒNG 2: BÁN XE KHÔNG TRẢ GÓP
Chọn xe ──► Chọn / tạo khách hàng ──► Tạo hợp đồng ──► Tính giá (phụ kiện, khuyến mãi)
    ──► Thanh toán một lần ──► Cập nhật trạng thái xe ──► In hợp đồng PDF ──► Hoàn tất

LUỒNG 3: BÁN XE TRẢ GÓP
Chọn xe ──► Chọn / tạo khách hàng ──► Tạo hợp đồng ──► Tính giá
    ──► Nhập thông tin trả góp (ngân hàng, lãi suất, thời hạn) ──► Tính số tiền hàng tháng
    ──► Lưu thông tin trả góp ──► Theo dõi thanh toán hàng tháng ──► Cảnh báo chậm trả

LUỒNG 4: BẢO HÀNH
Khách hàng mang xe đến ──► Tiếp nhận yêu cầu BH ──► Kiểm tra điều kiện BH
    ──► Phân loại miễn phí / tính phí ──► Thực hiện bảo hành ──► Ghi nhận chi phí ──► In phiếu BH

LUỒNG 5: BẢO DƯỠNG ĐỊNH KỲ
Hệ thống nhắc nhở trước hạn 7 ngày ──► Khách hàng đặt lịch ──► Thực hiện bảo dưỡng
    ──► Ghi nhận lịch sử BD ──► Cập nhật lịch tiếp theo

LUỒNG 6: MARKETING VÀ CHĂM SÓC
Tạo chiến dịch marketing ──► Thu thập lead ──► Chuyển đổi lead thành khách hàng
    ──► Ghi nhận mua hàng ──► Gửi ưu đãi tri ân ──► Khách hàng trở lại mua tiếp
```

---

## 6. Tổng kết chức năng theo nhóm nghiệp vụ

Các 71 chức năng trong hệ thống có thể được nhóm thành ba nhóm nghiệp vụ lớn theo thứ tự thời gian trong vòng đời khách hàng tại đại lý.

Nhóm nghiệp vụ tiền bán hàng bao gồm các module quản lý kho xe, quản lý nhà cung cấp và quản lý marketing. Đây là các nghiệp vụ chuẩn bị hàng hóa và tiếp cận khách hàng tiềm năng trước khi có giao dịch. Nhóm này chiếm 11 chức năng.

Nhóm nghiệp vụ bán hàng bao gồm các module quản lý xe, quản lý khách hàng, quản lý nhân viên, quản lý hợp đồng, quản lý phụ kiện, quản lý khuyến mãi và quản lý trả góp. Đây là các nghiệp vụ cốt lõi thực hiện giao dịch mua bán xe, chiếm 31 chức năng.

Nhóm nghiệp vụ hậu bán hàng bao gồm các module quản lý bảo hành, dịch vụ hậu mãi, quản lý khiếu nại và báo cáo thống kê. Đây là các nghiệp vụ chăm sóc khách hàng sau khi đã mua xe, giúp xây dựng mối quan hệ lâu dài và tạo doanh thu bổ sung, chiếm 20 chức năng.

Nhóm nghiệp vụ hệ thống bao gồm module bảo mật với 4 chức năng đảm bảo an toàn cho toàn bộ hoạt động của hệ thống.

---

*Ngày cập nhật: Tháng 5 năm 2026*