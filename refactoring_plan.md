# Tello Renewal 代码重构方案

## 当前代码结构分析

### 现有架构概览

```
src/tello_renewal/
├── __main__.py          # 入口点
├── cli/
│   └── commands.py      # CLI命令处理 (333行)
├── core/
│   ├── models.py        # 数据模型 (246行)
│   └── renewer.py       # 核心续费逻辑 (760行) ⚠️ 过大
├── notification/
│   └── email.py         # 邮件通知 (347行)
└── utils/
    ├── config.py        # 配置管理 (416行)
    └── logging.py       # 日志工具
```

### 主要问题识别

#### 1. **单一职责违反**

- `TelloWebClient` (760 行) 承担了太多责任：
  - 浏览器驱动管理
  - 网页元素定位和交互
  - 业务逻辑处理
  - 数据解析

#### 2. **代码重复**

- 浏览器配置逻辑在多个地方重复
- 元素等待和错误处理模式重复
- 点击策略代码冗余

#### 3. **可维护性问题**

- 硬编码的 CSS 选择器分散在代码中
- 网站结构变化需要修改多个地方
- 缺乏抽象层来处理网站交互

#### 4. **可测试性差**

- 大型类难以进行单元测试
- 网络依赖使测试复杂化
- 缺乏依赖注入

## 重构方案设计

### 1. 分层架构重构

```
src/tello_renewal/
├── __main__.py
├── cli/
│   └── commands.py
├── core/
│   ├── models.py
│   ├── engine.py           # 续费引擎 (业务逻辑)
│   └── services/
│       ├── __init__.py
│       ├── account.py      # 账户信息服务
│       ├── renewal.py      # 续费操作服务
│       └── balance.py      # 余额查询服务
├── web/
│   ├── __init__.py
│   ├── driver.py           # 浏览器驱动管理
│   ├── client.py           # Web客户端基类
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── base.py         # 页面基类
│   │   ├── login.py        # 登录页面
│   │   ├── dashboard.py    # 仪表板页面
│   │   └── renewal.py      # 续费页面
│   ├── elements/
│   │   ├── __init__.py
│   │   ├── locators.py     # 元素定位器
│   │   └── interactions.py # 交互策略
│   └── strategies/
│       ├── __init__.py
│       ├── click.py        # 点击策略
│       └── parsing.py      # 数据解析策略
├── notification/
│   └── email.py
└── utils/
    ├── config.py
    ├── logging.py
    └── exceptions.py       # 自定义异常
```

### 2. 核心组件重构

#### A. 浏览器驱动管理 (`web/driver.py`)

```python
class BrowserDriverManager:
    """统一的浏览器驱动管理器"""

    def create_driver(self, config: BrowserConfig) -> WebDriver
    def configure_proxy(self, driver: WebDriver, config: BrowserConfig)
    def setup_timeouts(self, driver: WebDriver, config: BrowserConfig)
```

#### B. 页面对象模式 (`web/pages/`)

```python
class BasePage:
    """页面基类，提供通用功能"""

    def wait_for_element(self, locator: Locator) -> WebElement
    def click_with_strategies(self, locator: Locator)
    def get_text_safe(self, locator: Locator) -> str

class LoginPage(BasePage):
    """登录页面"""

    def enter_credentials(self, email: str, password: str)
    def submit_login(self)
    def is_login_successful(self) -> bool

class DashboardPage(BasePage):
    """仪表板页面"""

    def get_renewal_date(self) -> date
    def get_current_balance(self) -> AccountBalance
    def get_plan_balance(self) -> AccountBalance
    def click_renew_button(self)
```

#### C. 元素定位器 (`web/elements/locators.py`)

```python
@dataclass
class Locator:
    """元素定位器"""
    by: str
    value: str
    description: str
    fallbacks: List['Locator'] = field(default_factory=list)

class TelloLocators:
    """Tello网站元素定位器集合"""

    # 登录页面
    LOGIN_EMAIL = Locator(By.ID, "i_username", "登录邮箱输入框")
    LOGIN_PASSWORD = Locator(By.ID, "i_current_password", "登录密码输入框")

    # 仪表板页面
    RENEWAL_DATE = Locator(By.CSS_SELECTOR, "span.card_text > span", "续费日期")

    # 余额相关 - 支持多个备选方案
    BALANCE_PACK_CARDS = Locator(
        By.CSS_SELECTOR,
        ".pack_card",
        "余额卡片",
        fallbacks=[
            Locator(By.CSS_SELECTOR, "div.pack_card", "余额卡片(div)")
        ]
    )
```

#### D. 交互策略 (`web/strategies/`)

```python
class ClickStrategy:
    """点击策略接口"""

    def click(self, driver: WebDriver, element: WebElement) -> bool

class MultiClickStrategy(ClickStrategy):
    """多重点击策略"""

    def __init__(self):
        self.strategies = [
            RegularClickStrategy(),
            JavaScriptClickStrategy(),
            ScrollAndClickStrategy(),
            JavaScriptScrollClickStrategy()
        ]

    def click(self, driver: WebDriver, element: WebElement) -> bool:
        for strategy in self.strategies:
            if strategy.click(driver, element):
                return True
        return False
```

#### E. 数据解析策略 (`web/strategies/parsing.py`)

```python
class BalanceParser:
    """余额解析器"""

    def parse_account_balance(self, elements: List[WebElement]) -> AccountBalance
    def parse_pack_card_balance(self, card_text: str) -> Optional[float]
    def parse_balance_details(self, details: List[WebElement]) -> Tuple[str, str, str]
```

#### F. 服务层 (`core/services/`)

```python
class AccountService:
    """账户信息服务"""

    def __init__(self, web_client: TelloWebClient):
        self.web_client = web_client

    def get_account_summary(self) -> AccountSummary
    def get_renewal_date(self) -> date
    def check_renewal_needed(self, renewal_date: date) -> bool

class BalanceService:
    """余额查询服务"""

    def get_current_balance(self) -> AccountBalance
    def get_plan_balance(self) -> AccountBalance
    def calculate_new_balance(self, current: AccountBalance, plan: AccountBalance) -> AccountBalance

class RenewalService:
    """续费操作服务"""

    def execute_renewal(self, dry_run: bool = False) -> RenewalResult
    def open_renewal_page(self)
    def fill_renewal_form(self, card_expiration: date)
    def submit_renewal(self, dry_run: bool = False) -> bool
```

### 3. 配置和异常处理

#### A. 自定义异常 (`utils/exceptions.py`)

```python
class TelloRenewalError(Exception):
    """基础异常类"""

class WebDriverError(TelloRenewalError):
    """浏览器驱动相关错误"""

class PageLoadError(TelloRenewalError):
    """页面加载错误"""

class ElementNotFoundError(TelloRenewalError):
    """元素未找到错误"""

class LoginError(TelloRenewalError):
    """登录失败错误"""

class RenewalError(TelloRenewalError):
    """续费操作错误"""
```

#### B. 配置增强

```python
class WebsiteConfig(BaseModel):
    """网站相关配置"""

    selectors_version: str = "v2"  # 选择器版本
    retry_count: int = 3
    element_timeout: int = 10
    fallback_enabled: bool = True
```

### 4. 重构优势

#### A. **单一职责**

- 每个类只负责一个特定功能
- 页面对象模式使页面逻辑清晰
- 服务层分离业务逻辑

#### B. **可维护性**

- 网站结构变化只需更新对应页面类
- 选择器集中管理，易于维护
- 策略模式使算法可替换

#### C. **可测试性**

- 小型类易于单元测试
- 依赖注入支持模拟测试
- 服务层可独立测试

#### D. **可扩展性**

- 新的交互策略易于添加
- 支持多版本选择器
- 插件化架构支持功能扩展

#### E. **错误处理**

- 分层异常处理
- 详细的错误信息
- 优雅的降级策略

### 5. 迁移策略

#### 阶段 1：基础重构 (1-2 天)

1. 创建新的目录结构
2. 提取浏览器驱动管理
3. 创建页面基类和异常类

#### 阶段 2：页面对象化 (2-3 天)

1. 实现登录页面类
2. 实现仪表板页面类
3. 实现续费页面类
4. 迁移元素定位器

#### 阶段 3：策略模式 (1-2 天)

1. 实现点击策略
2. 实现解析策略
3. 重构交互逻辑

#### 阶段 4：服务层 (2-3 天)

1. 创建账户服务
2. 创建余额服务
3. 创建续费服务
4. 重构引擎类

#### 阶段 5：测试和优化 (1-2 天)

1. 添加单元测试
2. 集成测试
3. 性能优化
4. 文档更新

### 6. 风险评估

#### 低风险

- 基础结构重构
- 异常处理改进
- 配置增强

#### 中风险

- 页面对象模式迁移
- 服务层重构

#### 高风险

- 核心业务逻辑变更
- 选择器大规模修改

### 7. 成功指标

1. **代码质量**

   - 单个文件不超过 200 行
   - 圈复杂度降低 50%
   - 代码重复率<5%

2. **可维护性**

   - 新功能开发时间减少 30%
   - Bug 修复时间减少 50%
   - 代码审查时间减少 40%

3. **可测试性**

   - 单元测试覆盖率>80%
   - 集成测试覆盖率>90%
   - 测试执行时间<5 分钟

4. **稳定性**
   - 网站结构变化适应时间<1 小时
   - 系统可用性>99.5%
   - 错误恢复时间<10 分钟

## 总结

这个重构方案将大幅提升代码的可维护性、可测试性和可扩展性。通过分层架构、页面对象模式和策略模式，我们可以创建一个更加健壮和灵活的系统，能够更好地应对未来的网站结构变化和功能需求。

重构将分阶段进行，确保在每个阶段都能保持系统的正常运行，降低风险并提供持续的价值。
