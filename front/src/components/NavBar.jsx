import { useState } from 'react';
import { NavLink } from 'react-router-dom';

function NavBar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <nav className="bg-blue-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-xl font-bold">测试报告系统</span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <NavLink 
                  to="/" 
                  className={({isActive}) => 
                    isActive 
                      ? "bg-blue-900 px-3 py-2 rounded-md text-sm font-medium" 
                      : "px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800"
                  }
                >
                  仪表盘
                </NavLink>
                <NavLink 
                  to="/reports" 
                  className={({isActive}) => 
                    isActive 
                      ? "bg-blue-900 px-3 py-2 rounded-md text-sm font-medium" 
                      : "px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800"
                  }
                >
                  测试报告
                </NavLink>
                <NavLink 
                  to="/measurements" 
                  className={({isActive}) => 
                    isActive 
                      ? "bg-blue-900 px-3 py-2 rounded-md text-sm font-medium" 
                      : "px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800"
                  }
                >
                  测量数据
                </NavLink>
                <NavLink 
                  to="/xml-import" 
                  className={({isActive}) => 
                    isActive 
                      ? "bg-blue-900 px-3 py-2 rounded-md text-sm font-medium" 
                      : "px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800"
                  }
                >
                  XML导入
                </NavLink>
              </div>
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              onClick={toggleMobileMenu}
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-white hover:bg-blue-800 focus:outline-none"
              aria-controls="mobile-menu"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              {isMobileMenuOpen ? (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 移动端导航菜单 */}
      <div
        className={`${isMobileMenuOpen ? 'block' : 'hidden'} md:hidden`}
        id="mobile-menu"
      >
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          <NavLink
            to="/"
            className={({isActive}) =>
              isActive
                ? "bg-blue-900 block px-3 py-2 rounded-md text-base font-medium"
                : "block px-3 py-2 rounded-md text-base font-medium hover:bg-blue-800"
            }
            onClick={() => setIsMobileMenuOpen(false)}
          >
            仪表盘
          </NavLink>
          <NavLink
            to="/reports"
            className={({isActive}) =>
              isActive
                ? "bg-blue-900 block px-3 py-2 rounded-md text-base font-medium"
                : "block px-3 py-2 rounded-md text-base font-medium hover:bg-blue-800"
            }
            onClick={() => setIsMobileMenuOpen(false)}
          >
            测试报告
          </NavLink>
          <NavLink
            to="/measurements"
            className={({isActive}) =>
              isActive
                ? "bg-blue-900 block px-3 py-2 rounded-md text-base font-medium"
                : "block px-3 py-2 rounded-md text-base font-medium hover:bg-blue-800"
            }
            onClick={() => setIsMobileMenuOpen(false)}
          >
            测量数据
          </NavLink>
          <NavLink
            to="/xml-import"
            className={({isActive}) =>
              isActive
                ? "bg-blue-900 block px-3 py-2 rounded-md text-base font-medium"
                : "block px-3 py-2 rounded-md text-base font-medium hover:bg-blue-800"
            }
            onClick={() => setIsMobileMenuOpen(false)}
          >
            XML导入
          </NavLink>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;
